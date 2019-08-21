#include <cmath>
#include <vector>

const double G = 6.674384e-11;


class Vector3 {
public:
    double x, y, z;

    Vector3(): x(0.0), y(0.0), z(0.0) {};
    Vector3(double x, double y, double z): x(x), y(y), z(z) {};
    Vector3(const Vector3 & other): x(other.x), y(other.y), z(other.z) {};

    void clear() {
        x = 0.0;
        y = 0.0;
        z = 0.0;
    };

    Vector3 operator+(const Vector3 & other) const {
        return Vector3(x + other.x, y + other.y, z + other.z);
    };

    Vector3 operator-(const Vector3 & other) const {
        return Vector3(x - other.x, y - other.y, z - other.z);
    };

    Vector3& operator+=(const Vector3 & other) {
        x += other.x;
        y += other.y;
        z += other.z;
        return *this;
    };

    Vector3& operator-=(const Vector3 & other) {
        x -= other.x;
        y -= other.y;
        z -= other.z;
        return *this;
    };

    Vector3 operator*(const double other) const {
        return Vector3(x * other, y * other, z * other);
    };

    Vector3 operator/(const double other) const {
        return Vector3(x / other, y / other, z / other);
    };

    Vector3& operator*=(const double other) {
        x *= other;
        y *= other;
        z *= other;
        return *this;
    };

    Vector3& operator/=(const double other) {
        x /= other;
        y /= other;
        z /= other;
        return *this;
    };
};


class Body {
public:
    double mass;
    Vector3 position;
    Vector3 velocity;

    Body(): mass(0.0), position(), velocity() {};

    Body(double mass, Vector3& position, Vector3& velocity):
        mass(mass), position(position), velocity(velocity) {};
};


class NBody {
public:
    NBody() {};
    void move(double dt);

    std::vector<Body> bodies;
private:
    std::vector<Vector3> forces;
};


void NBody::move(double dt) {
    auto n = bodies.size();

    if (forces.size() != n) {
        forces.resize(n);
    }
    for (auto it = forces.begin(); it != forces.end(); it++) {
        it->clear();
    }

    for (auto i=0; i < n; i++) {
        for (auto j=0; j < n; j++) {
            if (i != j) {
                /*
                   dist vector = position vector[i] - position vector[j]

                                       dist vector
                   dist unit vector = -------------
                                      |dist vector|

                                 mass[i] * mass[j]
                   |force| = G * -----------------
                                  |dist vector|^2

                   force vector = |force| * dist unit vector
                */

                auto dist_v = bodies[i].position - bodies[j].position;
                auto dist_modsq = dist_v.x * dist_v.x + dist_v.y * dist_v.y + dist_v.z * dist_v.z;
                auto dist_mod = sqrt(dist_modsq);
                auto force_mod = G * bodies[i].mass * bodies[j].mass / dist_modsq;
                auto force_v = dist_v / (dist_mod / force_mod);
                forces[i] += force_v;
                forces[j] -= force_v;
            }
        }
    }

    for (size_t i=0; i < n; i++) {
        auto& bi = bodies[i];
        auto dv = forces[i] / (bi.mass / dt);
        auto ds = (bi.velocity + dv / 2.0) * dt;
        bi.position += ds;
        bi.velocity += dv;
    }
}
