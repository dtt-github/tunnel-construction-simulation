"""Density-coupled volume correction for Newton's implicit MPM.

Newton tracks the volume of each particle through its elastic strain, which follows the grid velocity at the particle;
nothing ties it to how densely the particles sit. Where a solid stirs a confined material the particles bunch without
their strain recording it, spread again under their own pressure, and the material ends up believing it has expanded:
a sealed, pressurised paste loses its pressure (newton#5180; diagnostics/moving_collider_box.py).

The correction compares, around every grid node or cell, the volume the particles claim (rest volume times det Fe)
with the free volume there (the domain less the solids), and moves each particle's ln det Fe by -rate times the
logarithm of their ratio. It is for confined material: next to a free surface the cells are under-full and the
correction relieves their compression, which is what a free surface does, but it has only been tested confined.

Status: a partial remedy, off by default. Sealed box with a paddle, 197 kPa prestress: 20-31 kPa left without it,
184-190 kPa with it at 240 steps/s, 60-130 kPa at 60 steps/s. EPB chamber (60 steps/s, 6 s of excavation, interior
nodes only): 144-157 kPa against 33 kPa without it and 200 kPa with the chamber's regional volume balance, which
stays the default there. Next to a wall the free volume cannot be measured reliably (the grid's effective wall is not
the geometric one and particles sit in the contact layer), so the wall layers still take up material.
"""
from __future__ import annotations

import numpy as np


class VolumeCorrection:
    """lo, hi: corners of the box of grid cells (voxel across) that holds the material; solid(points) -> bool array,
    True inside a solid, called every step with the current pose of the solids, on the sample points outside the
    fixed solids static(points) (called once); rate: fraction of the mismatch removed
    per step; support: "node" gathers on grid nodes with trilinear weights, "cell" on cells with each particle spread
    over a cube of its own size; samples: free-volume sample points per voxel edge."""

    def __init__(self, voxel: float, lo, hi, solid, rate: float = 0.1, support: str = "node", samples: int = 4, limit: float = 0.02, static=None, interior: bool = False, fill: int = 6):
        self.dx, self.lo = float(voxel), np.asarray(lo, float)
        self.nc = np.maximum(np.ceil((np.asarray(hi, float) - self.lo) / self.dx - 1e-9).astype(int), 1)
        self.solid, self.rate, self.support, self.limit = solid, rate, support, limit
        self.interior, self.fill = interior, fill
        hs = self.dx / samples
        ax = [self.lo[k] + hs / 2 + hs * np.arange(self.nc[k] * samples) for k in range(3)]
        smp = np.stack(np.meshgrid(*ax, indexing="ij"), -1).reshape(-1, 3)
        self.dv = hs**3
        i_all, w_all = self._weights(smp, hs)
        self.full = np.bincount(i_all.ravel(), weights=w_all.ravel() * self.dv, minlength=self._size())  # no solids at all
        self.smp = smp[~static(smp)] if static is not None else smp
        self.s_idx, self.s_w = self._weights(self.smp, hs)
        self.spc0 = np.bincount(self.s_idx.ravel(), weights=self.s_w.ravel() * self.dv, minlength=self._size())
        self.v_rest = None
        self.stats: dict = {}

    def _size(self) -> int:
        return int(np.prod(self.nc + 1 if self.support == "node" else self.nc))

    def _weights(self, x: np.ndarray, width: float):
        """(8, n) flat indices and weights of each point on the nodes (trilinear) or cells (cube of the given width)."""
        g = (x - self.lo) / self.dx
        if self.support == "node":
            n = self.nc + 1
            g = np.clip(g, 0, self.nc - 1e-6)
            b = g.astype(int)
            f = g - b
        else:  # cells b and b + 1 share the cube [g - a, g + a], a = width / 2 voxel
            n = self.nc
            a = 0.5 * width / self.dx
            b = np.floor(g - a).astype(int)
            f = np.clip((g + a - (b + 1)) / (2 * a), 0.0, 1.0)
        idx, wts = [], []
        for c in range(8):
            o = np.array([(c >> 2) & 1, (c >> 1) & 1, c & 1])
            m = b + o
            inside = np.all((m >= 0) & (m < n), axis=1)
            m = np.clip(m, 0, n - 1)
            idx.append((m[:, 0] * n[1] + m[:, 1]) * n[2] + m[:, 2])
            wts.append(np.prod(np.where(o == 1, f, 1 - f), axis=1) * inside)
        return np.array(idx), np.array(wts)

    def _trusted(self, spc: np.ndarray, mat: np.ndarray) -> np.ndarray:
        """Nodes or cells whose mismatch is used. With interior set, only those clear of every solid: next to a wall
        the grid's effective wall is not the geometric one and particles sit in the contact layer, so the free volume
        there is wrong by a large fraction of a cell."""
        if self.interior:
            return (spc >= 0.98 * self.full) & (self.full >= 0.98 * self.dx**3) & (mat > 0)
        return (spc > 0.05 * self.dx**3) & (mat > 0)

    def _spread(self, dl: np.ndarray, good: np.ndarray) -> np.ndarray:
        """Mismatch carried from the trusted nodes or cells to their neighbours, self.fill layers deep."""
        n = self.nc + 1 if self.support == "node" else self.nc
        d, k = dl.reshape(n).copy(), good.reshape(n).copy()
        for _ in range(self.fill):
            num, den = np.zeros(n), np.zeros(n)
            for ax in range(3):
                for sh in (1, -1):
                    dd, kk = np.roll(d * k, sh, ax), np.roll(k, sh, ax).astype(float)
                    edge = [slice(None)] * 3
                    edge[ax] = 0 if sh == 1 else -1
                    dd[tuple(edge)], kk[tuple(edge)] = 0.0, 0.0
                    num += dd
                    den += kk
            new = ~k & (den > 0)
            d[new] = num[new] / den[new]
            k |= new
        return d.ravel()

    def free_volume(self) -> np.ndarray:
        cov = self.solid(self.smp)  # few samples are covered by the moving solids: subtract them from the fixed part
        return np.maximum(self.spc0 - np.bincount(self.s_idx[:, cov].ravel(), weights=self.s_w[:, cov].ravel() * self.dv, minlength=self._size()), 0.0)

    def calibrate(self, x: np.ndarray, fe: np.ndarray, active: np.ndarray, h: float) -> None:
        """Fix each particle's rest volume so that the material fills the free volume as it stands, strain included.
        Call it on a state whose strain is right (before a first solver step can lose any of it)."""
        det = np.linalg.det(fe)
        ok = active & np.isfinite(det) & (det > 0)
        idx, w = self._weights(x[ok], h)
        spc = self.free_volume()
        v = np.full(int(ok.sum()), h**3)
        for _ in range(3):  # particle volumes fitted to the free volume around them
            mat = np.bincount(idx.ravel(), weights=(w * v).ravel(), minlength=self._size())
            ratio = np.where(self._trusted(spc, mat) if self.interior else mat > 0, spc / np.maximum(mat, 1e-30), 1.0)
            v *= np.clip((w * ratio[idx]).sum(0) / np.maximum(w.sum(0), 1e-30), 0.5, 2.0)
        self.v_rest = np.full(len(x), h**3)
        self.v_rest[ok] = v / det[ok]

    def apply(self, x: np.ndarray, fe: np.ndarray, active: np.ndarray, h: float) -> np.ndarray:
        """Corrected elastic deformation gradients (n, 3, 3). x: particle positions, h: particle spacing. Calibrates on
        the first call if calibrate() was not called."""
        if self.v_rest is None:
            self.calibrate(x, fe, active, h)
        det = np.linalg.det(fe)
        ok = active & np.isfinite(det) & (det > 0)
        idx, w = self._weights(x[ok], h)
        spc = self.free_volume()
        mat = np.bincount(idx.ravel(), weights=(w * (self.v_rest[ok] * det[ok])).ravel(), minlength=self._size())
        good = self._trusted(spc, mat)
        dl = np.where(good, np.log(np.maximum(mat, 1e-30) / np.maximum(spc, 1e-30)), 0.0)
        if self.interior:
            dl = self._spread(dl, good)
        dp = (w * dl[idx]).sum(0) / np.maximum(w.sum(0), 1e-30)
        shift = np.clip(-self.rate * dp, -self.limit, self.limit)
        out = fe.copy()
        out[ok] *= np.exp(shift / 3.0)[:, None, None]
        self.last = (ok, dp, float(mat[good].sum() / max(spc[good].sum(), 1e-30)), float(mat[~good].sum() / max(mat.sum(), 1e-30)))  # for diagnostics
        self.stats = {"mismatch_mean": float(dp.mean()), "mismatch_rms": float(np.sqrt((dp**2).mean())), "clipped": int((abs(self.rate * dp) > self.limit).sum())}
        return out
