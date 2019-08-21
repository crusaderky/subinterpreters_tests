#include <algorithm>
#include <assert.h>
#include <cmath>
#include <immintrin.h>


const double G = 6.674384e-11;


class Body {
public:
    Body(double mass, double sx, double sy, double sz, double vx, double vy, double vz):
        mass(mass),
        sx(sx), sy(sy), sz(sz),
        vx(vx), vy(vy), vz(vz) {};

    double mass;
    double sx, sy, sz;
    double vx, vy, vz;
};


class NBody {
public:
    NBody(size_t n): n(n) {
        // Align for AVX512
        size_t stride = n % 8 == 0 ? n : n + 8 - n % 8;
        buf = new double[stride * 10 + 7];
        double * buf0 = ((size_t)buf % 8 == 0) ? buf : (double *)(((size_t)buf + 8 - (size_t)buf % 8));
        mass = buf0 + stride * 0;
        sx = buf0 + stride * 1;
        sy = buf0 + stride * 2;
        sz = buf0 + stride * 3;
        vx = buf0 + stride * 4;
        vy = buf0 + stride * 5;
        vz = buf0 + stride * 6;
        fx = buf0 + stride * 7;
        fy = buf0 + stride * 8;
        fz = buf0 + stride * 9;
    };

    ~NBody() {
        delete[] buf;
    };

    Body get(size_t i) {
        assert (i < n);
        return Body(mass[i], sx[i], sy[i], sz[i], vx[i], vy[i], vz[i]);
    };

    void set(size_t i, Body& b) {
        assert (i < n);
        mass[i] = b.mass;
        sx[i] = b.sx;
        sy[i] = b.sy;
        sz[i] = b.sz;
        vx[i] = b.vx;
        vy[i] = b.vy;
        vz[i] = b.vz;
    };

    void move(double dt);

    size_t n;
    double *mass;
    double *sx, *sy, *sz;
    double *vx, *vy, *vz;

private:
    double *fx, *fy, *fz;
    double *buf;
};


void NBody::move(double dt) {
    std::fill(fx, fz + n, 0.0);

    /*
       For every (i, j) where i != j:

       dist vector = position vector[i] - position vector[j]

                           dist vector
       dist unit vector = -------------
                          |dist vector|

                     mass[i] * mass[j]
       |force| = G * -----------------
                      |dist vector|^2

       force vector = |force| * dist unit vector
    */

    for (size_t i = 0; i < n; i++) {
        double mass_i_by_G = G * mass[i];

        for (size_t j = 0; j < n; j+= 8) {
            __m512d dx = sx[i] - *(__m512d*)(sx + j);
            __m512d dy = sy[i] - *(__m512d*)(sy + j);
            __m512d dz = sz[i] - *(__m512d*)(sz + j);
            __m512d dist_mod_sq = dx * dx + dy * dy + dz * dz;
            __m512d dist_mod_repr = _mm512_rsqrt28_pd(dist_mod_sq);  // 1.0 / sqrt(dist_mod_sq)

            __m512d force_scale = mass_i_by_G * *(__m512d*)(mass + j) / dist_mod_sq * dist_mod_repr;
            auto ij_delta = (int)i - (int)j;
            if (ij_delta >= 0 && ij_delta < 8) {
                force_scale[ij_delta] = 0.0;
            }
            for (auto i = n - j; i < 8; i++) {
                force_scale[i] = 0.0;
            }

            __m512d force_x = dx * force_scale;
            __m512d force_y = dy * force_scale;
            __m512d force_z = dz * force_scale;
            fx[i] += _mm512_reduce_add_pd(force_x);
            fy[i] += _mm512_reduce_add_pd(force_y);
            fz[i] += _mm512_reduce_add_pd(force_z);
            *(__m512d*)(fx + j) -= force_x;
            *(__m512d*)(fy + j) -= force_y;
            *(__m512d*)(fz + j) -= force_z;
        }
    }

    for (size_t i = 0; i < n; i+= 8) {
        __m512d force_scale = dt / *(__m512d*)(mass + i);

        __m512d dvxi = *(__m512d*)(fx + i) * force_scale;
        __m512d dvyi = *(__m512d*)(fy + i) * force_scale;
        __m512d dvzi = *(__m512d*)(fz + i) * force_scale;

        __m512d dsxi = (*(__m512d*)(vx + i) + 0.5 * dvxi) * dt;
        __m512d dsyi = (*(__m512d*)(vy + i) + 0.5 * dvyi) * dt;
        __m512d dszi = (*(__m512d*)(vz + i) + 0.5 * dvzi) * dt;

        *(__m512d*)(vx + i) += dvxi;
        *(__m512d*)(vy + i) += dvyi;
        *(__m512d*)(vz + i) += dvzi;
        *(__m512d*)(sx + i) += dsxi;
        *(__m512d*)(sy + i) += dsyi;
        *(__m512d*)(sz + i) += dszi;
    }
}
