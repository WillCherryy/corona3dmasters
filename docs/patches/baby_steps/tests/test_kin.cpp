// Scratch unit test (not part of the model): energy accounting of Particle::do_collision with an energy loss
#include <vector>
#include <iostream>
#include <sstream>
#include <fstream>
#include <memory>
#include <algorithm>
#include <cmath>
#include <string>
#include <random>
#include </opt/local/include/eigen3/Eigen/Core>
#define private public
#define protected public
#include "Particle_H.hpp"
#include "Particle_CO2.hpp"
#include "Common_Functions.hpp"
#undef private
#undef protected
using namespace std;
using namespace Eigen;
int main()
{
	mt19937 g(5); normal_distribution<double> nd(0.0, 1.0);
	double worst_E = 0.0, worst_ang = 0.0, worst_mom = 0.0; int n_inel = 0;
	for (int trial=0; trial<4000; trial++)
	{
		auto h = make_shared<Particle_H>(); auto t = make_shared<Particle_CO2>();
		double vh = 1.38e6 * (0.3 + 3.0*(trial%7)/7.0);
		Vector3d dir(nd(g), nd(g), nd(g)); dir.normalize();
		h->velocity = vh*dir; t->velocity = Vector3d(3e4*nd(g), 3e4*nd(g), 3e4*nd(g));
		double m1 = h->get_mass(), m2 = t->get_mass();
		Vector3d vcm = (m1*h->velocity + m2*t->velocity)/(m1+m2); Vector3d r = h->velocity.normalized();
		double Ecm0 = 0.5*m1*(h->velocity-vcm).squaredNorm() + 0.5*m2*(t->velocity-vcm).squaredNorm();
		double dE_eV = (trial%2==0) ? 0.0 : 0.4*Ecm0/constants::ergev*(0.05 + 0.9*((trial/2)%5)/5.0);
		double theta = 0.1 + 3.0*((trial/7)%10)/10.0;
		Vector3d p0 = m1*h->velocity + m2*t->velocity;
		h->do_collision(t, theta, 0.0, 3.397e8, dE_eV);
		Vector3d vrel = h->velocity - vcm; double Ecm1 = 0.5*m1*vrel.squaredNorm()*(1.0 + m1/m2);
		Vector3d p1 = m1*h->velocity + m2*(vcm - (m1/m2)*vrel);
		worst_E = max(worst_E, fabs(Ecm1 - (Ecm0 - dE_eV*constants::ergev))/Ecm0);
		worst_ang = max(worst_ang, fabs(vrel.normalized().dot(r) - cos(theta)));
		worst_mom = max(worst_mom, (p1-p0).norm()/p0.norm()); if (dE_eV > 0) n_inel++;
	}
	printf("%d collisions (%d with an energy loss of 2-36 %% of E_cm): worst relative error of E_cm after = E_cm before - dE: %.2e; worst |cos(angle to incident direction) - cos(theta)|: %.2e; worst momentum error: %.2e\n", 4000, n_inel, worst_E, worst_ang, worst_mom);
	return 0;
}
