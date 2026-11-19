// Scratch unit test (not part of the model): channel sampling, angle sampling, and the energy accounting of do_collision.
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
#include "Background_Species.hpp"
#include "Particle_H.hpp"
#include "Particle_CO2.hpp"
#include "Planet.hpp"
#undef private
#undef protected
using namespace std;
using namespace Eigen;

int main()
{
	Planet pl; pl.init(6.4185e26, 3.397e8);
	string cfgs[1] = {"./inputs/CO2_Mars_HotH_HCO2channels.cfg"};
	Background_Species bg(1, cfgs, pl, 200.0, 1.0e7, "", "", 0.0, 0.0);
	cout << "channels read: " << bg.num_channels[0] << ", table energies: " << bg.channel_E[0].size() << "\n";

	cout << "\n=== TEST 1: channel sampling (4e6 draws per energy): E_eV, freq of channels j'=0,2,4,6,8,10 (%), P(j'>52) (%), mean energy loss (meV)\n";
	for (double E : {0.1, 0.35, 1.0, 3.0, 5.0})
	{
		vector<long> cnt(71, 0); double sdE = 0.0; long N = 4000000;
		for (long i=0; i<N; i++) { int c = bg.pick_channel(0, E); cnt[c]++; sdE += bg.channel_dE[0][c]; }
		long hi = 0; for (int c=27; c<71; c++) hi += cnt[c];
		printf("E=%.2f:", E); for (int c=0; c<6; c++) printf(" %.3f", 100.0*cnt[c]/N); printf("  | %.3f | %.3f\n", 100.0*hi/N, 1000.0*sdE/N);
	}

	cout << "\n=== TEST 2: angle sampling (2e6 draws): channel j', E_eV, mean(1-cos theta)\n";
	for (double E : {1.0, 5.0})
		for (int c : {0, 1, 5, 12, 26, 40})
		{
			double s = 0.0; long N = 2000000;
			for (long i=0; i<N; i++) s += 1.0 - cos(bg.find_new_theta_channel(0, c, E));
			printf("j'=%d E=%.1f: %.4f\n", 2*c, E, s/N);
		}

	cout << "\n=== TEST 3: energy accounting of Particle::do_collision (H on CO2, thermal CO2)\n";
	mt19937 g(5); normal_distribution<double> nd(0.0, 1.0);
	double worst_E = 0.0, worst_ang = 0.0, worst_mom = 0.0;
	for (int trial=0; trial<2000; trial++)
	{
		auto h = make_shared<Particle_H>(); auto t = make_shared<Particle_CO2>();
		double vh = 1.38e6 * (0.3 + 3.0*(trial%7)/7.0);                 // 0.1 to about 10 eV
		Vector3d dir(nd(g), nd(g), nd(g)); dir.normalize();
		h->velocity = vh*dir;
		t->velocity = Vector3d(3e4*nd(g), 3e4*nd(g), 3e4*nd(g));
		double m1 = h->get_mass(), m2 = t->get_mass();
		Vector3d vcm = (m1*h->velocity + m2*t->velocity)/(m1+m2);
		Vector3d r = h->velocity.normalized();
		double Ecm0 = 0.5*m1*(h->velocity-vcm).squaredNorm() + 0.5*m2*(t->velocity-vcm).squaredNorm();   // erg
		double dE_eV = (trial%3==0) ? 0.0 : 0.4*Ecm0/constants::ergev*(0.1 + 0.8*((trial/3)%5)/5.0);   // 0, or 4-36 % of E_cm
		double theta = 0.1 + 3.0*((trial/7)%10)/10.0;
		Vector3d p0 = m1*h->velocity + m2*t->velocity;
		h->do_collision(t, theta, 0.0, 3.397e8, dE_eV);
		Vector3d vrel = h->velocity - vcm;
		double Ecm1 = 0.5*m1*vrel.squaredNorm()*(1.0 + m1/m2);
		Vector3d v2new = vcm - (m1/m2)*vrel;                              // partner velocity from momentum conservation
		Vector3d p1 = m1*h->velocity + m2*v2new;
		worst_E = max(worst_E, fabs(Ecm1 - (Ecm0 - dE_eV*constants::ergev))/Ecm0);
		worst_ang = max(worst_ang, fabs(vrel.normalized().dot(r) - cos(theta)));
		worst_mom = max(worst_mom, (p1-p0).norm()/p0.norm());
	}
	printf("worst relative error of E_cm after = E_cm before - dE: %.2e; worst |cos(angle to incident direction) - cos(theta)|: %.2e; worst momentum error: %.2e\n", worst_E, worst_ang, worst_mom);
	return 0;
}
