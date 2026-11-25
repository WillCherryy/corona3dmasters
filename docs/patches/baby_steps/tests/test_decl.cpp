// Scratch unit test (not part of the model): the declaration of the collision type against the cross-section tables
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
#include "Planet.hpp"
#undef private
#undef protected
using namespace std;
int main()
{
	Planet pl; pl.init(6.4185e26, 3.397e8);
	string cfgs[1] = {"./inputs/CO2_Mars_HotH_decl.cfg"};
	Background_Species bg(1, cfgs, pl, 200.0, 1.0e7, "", "", 0.0, 0.0);
	cout << "energy eV: table inelastic fraction (1 - sigma_el/sigma_tot) | declared inelastic fraction (4e6 draws)\n";
	for (double E : {0.01, 0.1, 0.35, 1.0, 3.0, 5.0, 8.0})
	{
		double tot = bg.sigma_interp[0]->linterp(E), el = bg.elastic_interp[0]->linterp(E);
		long N = 4000000, ninel = 0;
		for (long i=0; i<N; i++) if (bg.is_collision_inelastic(0, E, tot)) ninel++;
		printf("%5.2f: %.5f | %.5f\n", E, 1.0 - el/tot, (double)ninel/N);
	}
	return 0;
}
