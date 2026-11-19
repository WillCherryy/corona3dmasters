/*
 * Background_Species.hpp
 *
 *  Created on: Jun 29, 2020
 *      Author: rodney
 */

#ifndef BACKGROUND_SPECIES_HPP_
#define BACKGROUND_SPECIES_HPP_

#include <vector>
#include <iostream>
#include <sstream>
#include <fstream>
#include "Particle_CO.hpp"
#include "Particle_CO2.hpp"
#include "Particle_H.hpp"
#include "Particle_N2.hpp"
#include "Particle_O.hpp"
#include "Distribution_MB.hpp"
#include "Planet.hpp"
#include "Common_Functions.hpp"
#include "Interpolator.hpp"
using namespace std;

class Background_Species {
public:
	Background_Species();
	Background_Species(int num_parts, string config_files[], Planet p, double ref_T, double ref_h, string temp_profile_filename, string dens_profile_filename, double profile_bottom, double profile_top);
	virtual ~Background_Species();
	bool check_collision(shared_ptr<Particle> p, double dt);
	int get_num_collisions();
	shared_ptr<Particle> get_collision_target();
	double get_collision_theta();
	double get_collision_dE();        // energy (eV) removed from the relative motion by the next collision (0 = elastic)
	void print_channel_stats();       // collisions per channel and mean energy loss, for species that have channels

private:
	bool use_temp_profile;       // flag for whether or not temperature profile is available
	bool use_dens_profile;       // flag for whether or not density profile is available
	int num_species;             // number of background species in atmosphere
	int num_collisions;          // tracks total number of collisions during simulation
	int collision_target;        // index of particle in bg_parts to be used for next collision
	Planet my_planet;            // contains planet mass, radius, and gravitational constant
	double collision_theta;      // angle (in radians) to be used for next collision
	double collision_dE;         // energy loss (eV) of the next collision (0 = elastic)
	double ref_temp;             // temperature (in Kelvin) at reference height
	double ref_height;           // height (in cm above planet surface) to extrapolate densities from if no profile available
	double ref_g;                // acceleration due to gravity (G*M/r^2) at reference height
	shared_ptr<Distribution_MB> my_dist;    // distribution to be used for initialization of bg particles
	vector<shared_ptr<Particle>> bg_parts;  // array of pointers to child particle classes
	double profile_bottom_alt;            // altitude above surface (cm) where atmospheric profiles begin
	double profile_top_alt;               // altitude above surface (cm) where atmospheric profiles end
	vector<double> temp_alt_bins;         // altitude bins from imported temperature profile
	vector<double> Tn;                    // neutral species temperature profile
	shared_ptr<Interpolator> Tn_interp;   // interpolator for neutral temp profile
	vector<double> Ti;                    // ionic species temperature profile
	shared_ptr<Interpolator> Ti_interp;   // interpolator for ion temp profile
	vector<double> Te;                    // electron temperature profile
	shared_ptr<Interpolator> Te_interp;   // interpolator for electron temp profile
	vector<double> dens_alt_bins;         // array of altitude bins imported along with densities
	vector<vector<double>> bg_densities;  // array of densities for each particle in bg_parts
	vector<shared_ptr<Interpolator>> dens_interp;  // density interpolator objects
	vector<double> bg_sigma_defaults;     // array of default total cross sections for each particle
	vector<vector<vector<double>>> bg_sigma_tables;  // lookup tables for total cross sections
	vector<shared_ptr<Interpolator>> sigma_interp;  // total sigma interpolator objects
	vector<vector<double>> bg_scaleheights;       // array of scale heights for each particle type
	vector<vector<double>> bg_avg_v;      // array of average (thermal) velocities for each particle
	vector<shared_ptr<Interpolator>> avg_v_interp;   // avg_v interpolator objects
	vector<vector<double>> diff_sigma_energies;              // array of available differential cross section energies for each species
	vector<vector<vector<vector<double>>>> diff_sigma_CDFs;  // CDFs built from imported differential cross section tables; used for looking up scattering angles

	// collision channels (e.g. final rotational levels of CO2); num_channels[species] = 0 means an ordinary single-channel species
	vector<int> num_channels;                                    // channels per species
	vector<vector<double>> channel_dE;                           // [species][channel] energy loss (eV)
	vector<vector<double>> channel_E;                            // [species][k] energy grid (eV) of the channel cross-section table
	vector<vector<vector<double>>> channel_sigma;                // [species][channel][k] cross section (cm^2)
	vector<vector<vector<vector<vector<double>>>>> channel_CDFs; // [species][energy][channel][0 = CDF, 1 = angle][value]
	vector<vector<long>> channel_counts;                         // [species][channel] collisions sampled (diagnostics)
	vector<double> channel_dE_sum;                               // [species] summed energy loss (eV) of the sampled collisions (diagnostics)

	// returns collision energy in eV between particle 1 and particle 2
	double calc_collision_e(shared_ptr<Particle> p1, shared_ptr<Particle> p2);

	// calculates new density of background particle based on radial position and scale height
	double calc_new_density(double ref_density, double scale_height, double r_moved);

	// scans imported differential scattering CDF for new collision theta
	double find_new_theta(int part_index, double energy);

	// channels: choose the final channel of a collision at this energy (eV) / scattering angle for that channel / read and build the tables
	int pick_channel(int part_index, double energy);
	double find_new_theta_channel(int part_index, int channel, double energy);
	void make_channel_CDF(int part_index, int energy_index, int channel, vector<double> angle, vector<double> sigma);
	void read_channel_file(string filename, int n, int part_index);
	void read_columns(string filename, vector<vector<double>> &cols);

	// get density from imported density profile if available
	double get_density(double alt, int index);

	// make a new differential cross section CDF and store at diff_sigma_CDFs[index]
	void make_new_CDF(int part_index, int energy_index, vector<double> &angle, vector<double> &sigma);

	//subroutine to set particle type
	shared_ptr<Particle> set_particle_type(string type);
};

#endif /* BACKGROUND_SPECIES_HPP_ */
