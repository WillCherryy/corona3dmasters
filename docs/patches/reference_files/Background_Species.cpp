/*
 * Background_Species.cpp
 *
 *  Created on: Jun 29, 2020
 *      Author: rodney
 */

#include "Background_Species.hpp"
#include <algorithm>

Background_Species::Background_Species() {
	use_temp_profile = false;
	use_dens_profile = false;
	profile_bottom_alt = 0.0;
	profile_top_alt = 0.0;
	num_collisions = 0;
	num_species = 0;
	ref_temp = 0.0;
	ref_height = 0.0;
	ref_g = 0.0;
	collision_target = -1;
	collision_theta = 0.0;
	collision_dE = 0.0;
	my_dist = NULL;
}

Background_Species::Background_Species(int num_parts, string config_files[], Planet p, double ref_T, double ref_h, string temp_profile_filename, string dens_profile_filename, double profile_bottom, double profile_top)
{
	num_collisions = 0;
	num_species = num_parts;
	my_planet = p;
	ref_temp = ref_T;
	ref_height = ref_h;
	my_dist = make_shared<Distribution_MB>(my_planet, ref_height, ref_temp);
	profile_bottom_alt = profile_bottom;
	profile_top_alt = profile_top;
	collision_target = -1;   // set to -1 when no collision happening
	collision_theta = 0.0;
	collision_dE = 0.0;
	ref_g = (constants::G * my_planet.get_mass()) / (pow(my_planet.get_radius()+ref_height, 2.0));

	if (temp_profile_filename != "")
	{
		use_temp_profile = true;
	}
	else
	{
		use_temp_profile = false;
	}

	if (dens_profile_filename != "")
	{
		use_dens_profile = true;
	}
	else
	{
		use_dens_profile = false;
	}

	bg_parts.resize(num_species);
	bg_densities.resize(num_species);
	dens_interp.resize(num_species);
	bg_sigma_defaults.resize(num_species);
	bg_sigma_tables.resize(num_species);
	sigma_interp.resize(num_species);
	bg_scaleheights.resize(num_species);
	bg_avg_v.resize(num_species);
	avg_v_interp.resize(num_species);
	diff_sigma_energies.resize(num_species);
	diff_sigma_CDFs.resize(num_species);
	num_channels.assign(num_species, 0);
	channel_dE.resize(num_species);
	channel_E.resize(num_species);
	channel_sigma.resize(num_species);
	channel_CDFs.resize(num_species);
	channel_counts.resize(num_species);
	channel_dE_sum.assign(num_species, 0.0);
	for (int i=0; i<num_species; i++)
	{
		int num_energies = 0;
		int energies_index = 0;
		int num_channels_cfg = 0;           // channels listed in the species config (0 = ordinary single-channel species)
		string channel_file_cfg = "";
		bg_sigma_tables[i].resize(2);
		diff_sigma_CDFs[i].resize(2);

		ifstream infile;
		infile.open(config_files[i]);
		if (!infile.good())
		{
			cout << "Background species configuration file " + to_string(i+1) + " not found!\n";
			exit(1);
		}
		string line, param, val;
		vector<string> parameters;
		vector<string> values;
		int num_params = 0;

		while (getline(infile, line))
		{
			if (line[0] == '#' || line.empty() || std::all_of(line.begin(), line.end(), ::isspace))
			{
				continue;
			}
			else
			{
				stringstream str(line);
				str >> param >> val;
				parameters.push_back(param);
				values.push_back(val);
				num_params++;
				param = "";
				val = "";
			}
		}
		infile.close();

		for (int j=0; j<num_params; j++)
		{
			if (parameters[j] == "type")
			{
				bg_parts[i] = set_particle_type(values[j]);
			}
			else if (parameters[j] == "ref_dens")
			{
				bg_densities[i].push_back(stod(values[j]));
			}
			else if (parameters[j] == "total_sigma_default")
			{
				bg_sigma_defaults[i] = stod(values[j]);
			}
			else if (parameters[j] == "total_sigma_file")
			{
				if (values[j] != "")
				{
					bg_sigma_defaults[i] = 0.0;
					common::import_csv(values[j], bg_sigma_tables[i][0], bg_sigma_tables[i][1]);
					sigma_interp[i] = make_shared<Interpolator>(bg_sigma_tables[i][0], bg_sigma_tables[i][1]);
				}
			}
			else if (parameters[j] == "num_diff_energies")
			{
				num_energies = stoi(values[j]);
				energies_index = j+1;
				diff_sigma_CDFs[i].resize(num_energies);
			}
			else if (parameters[j] == "num_channels")
			{
				num_channels_cfg = stoi(values[j]);
			}
			else if (parameters[j] == "channel_file")
			{
				channel_file_cfg = values[j];
			}
		}
		bg_scaleheights[i].push_back(constants::k_b*ref_temp/(bg_parts[i]->get_mass()*ref_g));
		bg_avg_v[i].push_back(sqrt(constants::k_b*ref_temp/bg_parts[i]->get_mass()));

		if (num_channels_cfg > 0)
		{
			channel_CDFs[i].resize(num_energies);
		}
		for (int j=0; j<num_energies; j++)
		{
			diff_sigma_CDFs[i][j].resize(2);
			vector<vector<double>> diff_sigma_PDF;
			diff_sigma_PDF.resize(2);
			diff_sigma_energies[i].push_back(stod(values[energies_index + j]));
			common::import_csv(values[energies_index + num_energies + j], diff_sigma_PDF[0], diff_sigma_PDF[1]);
			make_new_CDF(i, j, diff_sigma_PDF[0], diff_sigma_PDF[1]);

			if (num_channels_cfg > 0)   // the angle file then holds the angle and one differential cross section per channel
			{
				vector<vector<double>> cols;
				read_columns(values[energies_index + num_energies + j], cols);
				if ((int)cols.size() != num_channels_cfg + 1)
				{
					cout << "\"" << values[energies_index + num_energies + j] << "\" must have 1 + num_channels columns!\n";
					exit(1);
				}
				channel_CDFs[i][j].resize(num_channels_cfg);
				for (int c=0; c<num_channels_cfg; c++)
				{
					make_channel_CDF(i, j, c, cols[0], cols[c+1]);
				}
			}
		}
		if (num_channels_cfg > 0)
		{
			read_channel_file(channel_file_cfg, num_channels_cfg, i);
			num_channels[i] = num_channels_cfg;
			channel_counts[i].assign(num_channels_cfg, 0);

			if (bg_sigma_defaults[i] == 0.0)   // a total cross-section table is in use: it must equal the sum of the channel cross sections
			{
				double worst = 0.0;
				for (size_t k=0; k<channel_E[i].size(); k++)
				{
					double sum = 0.0;
					for (int c=0; c<num_channels_cfg; c++)
					{
						sum += channel_sigma[i][c][k];
					}
					double tot = sigma_interp[i]->linterp(channel_E[i][k]);
					worst = max(worst, fabs(sum/tot - 1.0));
				}
				if (worst > 1.0e-3)
				{
					cout << "total_sigma_file and the channel table differ by up to " << worst << " (relative): total_sigma_file must be the TOTAL table (all channels)!\n";
					exit(1);
				}
			}
		}
	}

	// read in temperature profile (if available) and set avg_v for each alt bin for each species
	if (use_temp_profile)
	{
		common::import_csv(temp_profile_filename, temp_alt_bins, Tn, Ti, Te);
		Tn_interp = make_shared<Interpolator>(temp_alt_bins, Tn);
		Ti_interp = make_shared<Interpolator>(temp_alt_bins, Ti);
		Te_interp = make_shared<Interpolator>(temp_alt_bins, Te);
		int num_alt_bins = temp_alt_bins.size();
		for (int i=0; i<num_species; i++)
		{
			// clear avg_v based on ref_temp and populate with values based on temp profile
			bg_avg_v[i].clear();
			double mass = bg_parts[i]->get_mass();
			for (int j=0; j<num_alt_bins; j++)
			{
				bg_avg_v[i].push_back(sqrt(constants::k_b*Tn[j]/mass));
			}

			// generate interpolator for bg_avg_v for each species
			avg_v_interp[i] = make_shared<Interpolator>(temp_alt_bins, bg_avg_v[i]);
		}
	}

	// read in density profile (if available)
	if (use_dens_profile)
	{
		for (int i=0; i<num_species; i++)
		{
			// clear out default densities and scale heights in order to use profile derived values
			bg_densities[i].clear();
			bg_scaleheights[i].clear();
			bg_scaleheights[i].resize(2);
		}
		if (num_species == 5)
		{
			common::import_csv(dens_profile_filename, dens_alt_bins, bg_densities[0], bg_densities[1], bg_densities[2], bg_densities[3], bg_densities[4]);
		}
		else if (num_species == 4)
		{
			common::import_csv(dens_profile_filename, dens_alt_bins, bg_densities[0], bg_densities[1], bg_densities[2], bg_densities[3]);
		}
		else if (num_species == 3)
		{
			common::import_csv(dens_profile_filename, dens_alt_bins, bg_densities[0], bg_densities[1], bg_densities[2]);
		}
		else if (num_species == 2)
		{
			common::import_csv(dens_profile_filename, dens_alt_bins, bg_densities[0], bg_densities[1]);
		}
		else if (num_species == 1)
		{
			common::import_csv(dens_profile_filename, dens_alt_bins, bg_densities[0]);
		}

		double bottom_local_g = (constants::G * my_planet.get_mass()) / (pow(my_planet.get_radius()+profile_bottom_alt, 2.0));
		double top_local_g = (constants::G * my_planet.get_mass()) / (pow(my_planet.get_radius()+profile_top_alt, 2.0));
		for (int i=0; i<num_species; i++)
		{
			// generate interpolator for each density profile
			dens_interp[i] = make_shared<Interpolator>(dens_alt_bins, bg_densities[i]);

			// calc top and bottom scale height to be used for extrapolating densities
			bg_scaleheights[i][0] = constants::k_b*Tn_interp->loglinterp(profile_bottom_alt)/(bg_parts[i]->get_mass()*bottom_local_g);
			bg_scaleheights[i][1] = constants::k_b*Tn_interp->loglinterp(profile_top_alt)/(bg_parts[i]->get_mass()*top_local_g);
		}
	}
}


Background_Species::~Background_Species() {

}

// returns collision energy in eV between particle 1 and particle 2
double Background_Species::calc_collision_e(shared_ptr<Particle> p1, shared_ptr<Particle> p2)
{
	double e = 0.0;
	double p1_mass = p1->get_mass();
	double p2_mass = p2->get_mass();
	Matrix<double, 3, 1> p1_v = {p1->get_vx(), p1->get_vy(), p1->get_vz()};
	Matrix<double, 3, 1> p2_v = {p2->get_vx(), p2->get_vy(), p2->get_vz()};
	Matrix<double, 3, 1> vcm;
	vcm = (p1_mass*p1_v.array() + p2_mass*p2_v.array()) / (p1_mass + p2_mass);
	Matrix<double, 3, 1> p1_vcm = p1_v.array() - vcm.array();    // particle 1 c-o-m velocity
	Matrix<double, 3, 1> p2_vcm = p2_v.array() - vcm.array();    // particle 2 c-o-m velocity
	double p1_vcm_tot = sqrt(p1_vcm[0]*p1_vcm[0] + p1_vcm[1]*p1_vcm[1] + p1_vcm[2]*p1_vcm[2]);  // particle 1 c-o-m scalar velocity
	double p2_vcm_tot = sqrt(p2_vcm[0]*p2_vcm[0] + p2_vcm[1]*p2_vcm[1] + p2_vcm[2]*p2_vcm[2]);  // particle 2 c-o-m scalar velocity
	e = (0.5*p1_mass*p1_vcm_tot*p1_vcm_tot + 0.5*p2_mass*p2_vcm_tot*p2_vcm_tot) / constants::ergev;

	return e;
}

// calculates new density of background particle based on radial position and scale height
double Background_Species::calc_new_density(double ref_density, double scale_height, double r_moved)
{
	return ref_density*exp(r_moved/scale_height);
}

// check to see if a collision occurred and initialize target particle if so
bool Background_Species::check_collision(shared_ptr<Particle> p, double dt)
{
	vector<double> energy;
	energy.resize(num_species);
	double r = p->get_radius();
	double my_total_v = p->get_total_v();
	double alt = r - my_planet.get_radius();
	double r_moved = my_planet.get_radius() + ref_height - r;

	// get densities at current location
	vector<double> dens;
	dens.resize(num_species);

	if (use_dens_profile)  // get new density from imported density profile
	{
		for (int i=0; i<num_species; i++)
		{
			dens[i] = get_density(alt, i);
		}
	}
	else  // calculate new density based on reference scale height
	{
		for (int i=0; i<num_species; i++)
		{
			dens[i] = calc_new_density(bg_densities[i][0], bg_scaleheights[i][0], r_moved);
		}
	}

	// look up total cross sections to use for each species, or use default if no table available
	vector<double> total_sig;
	total_sig.resize(num_species);
	for (int i=0; i<num_species; i++)
	{
		double avg_v = 0.0;

		// if default sigma is zero, then table is available, must initialize a particle to get energy
		if (bg_sigma_defaults[i] == 0.0)
		{
			if (use_temp_profile)
			{
				if (alt < profile_bottom_alt)
				{
					avg_v = bg_avg_v[i][0];
				}
				else if (alt > profile_top_alt)
				{
					avg_v = bg_avg_v[i].back();
				}
				else
				{
					avg_v = avg_v_interp[i]->loglinterp(alt);
				}
			}
			else  // use reference temp avg_v
			{
				avg_v = bg_avg_v[i][0];
			}
			my_dist->init_vonly(bg_parts[i], avg_v);

			// calculate collision energy and look up cross section
			energy[i] = calc_collision_e(p, bg_parts[i]);
			total_sig[i] = sigma_interp[i]->linterp(energy[i]);
		}
		else  // just use default sigma if no lookup table available
		{
			total_sig[i] = bg_sigma_defaults[i];
		}
	}

	// determine if test particle collided
	double u = common::get_rand();
	double tau = 0.0;
	for (int i=0; i<num_species; i++)
	{
		tau += 	my_total_v*dt*total_sig[i]*dens[i];
	}
	if (u > exp(-tau))
	{
		num_collisions++;

		// pick target species for collision
		u = common::get_rand();
		// weight each species by its contribution to the collision depth, sigma_s * n_s
		double total_weight = 0.0;
		for (int i=0; i<num_species; i++)
		{
			total_weight += total_sig[i]*dens[i];
		}
		double frac = 0.0;
		collision_target = 0;

		do
		{
			frac += total_sig[collision_target]*dens[collision_target] / total_weight;
			collision_target++;
		}
		while (u >= frac && collision_target < num_species);

		// subtract the extra added integer, and initialize collision target if necessary
		collision_target--;

		if (bg_sigma_defaults[collision_target] != 0.0)  // particle needs to be initialized
		{
			if (use_temp_profile)
			{
				double avg_v = 0.0;
				if (alt < profile_bottom_alt)
				{
					avg_v = bg_avg_v[collision_target][0];
				}
				else if (alt > profile_top_alt)
				{
					avg_v = bg_avg_v[collision_target].back();
				}
				else
				{
					avg_v = avg_v_interp[collision_target]->loglinterp(alt);
				}
				my_dist->init_vonly(bg_parts[collision_target], avg_v);
			}
			else
			{
				my_dist->init_vonly(bg_parts[collision_target], bg_avg_v[collision_target][0]);
			}
			energy[collision_target] = calc_collision_e(p, bg_parts[collision_target]);
		}
		if (num_channels[collision_target] > 0)   // species with collision channels: pick the channel, then its angle and energy loss
		{
			int ch = pick_channel(collision_target, energy[collision_target]);
			collision_dE = channel_dE[collision_target][ch];
			collision_theta = find_new_theta_channel(collision_target, ch, energy[collision_target]);
			channel_counts[collision_target][ch]++;
			channel_dE_sum[collision_target] += collision_dE;
		}
		else
		{
			collision_dE = 0.0;
			collision_theta = find_new_theta(collision_target, energy[collision_target]);
		}
		return true;
	}
	else
	{
		collision_target = -1;
		collision_dE = 0.0;
		return false;
	}
}

// scans imported differential scattering CDF for new collision theta
double Background_Species::find_new_theta(int part_index, double energy)
{
	// get energy index
	int energy_index = 0;
	int num_energies = diff_sigma_energies[part_index].size();
	if (energy <= diff_sigma_energies[part_index][0])
	{
		energy_index = 0;
	}
	else if (energy >= diff_sigma_energies[part_index].back())
	{
		energy_index = num_energies - 1;
	}
	else
	{
		double difference = INFINITY;
		for (int i=0; i<num_energies; i++)
		{
			double new_diff = abs(energy - diff_sigma_energies[part_index][i]);
			if (new_diff < difference)
			{
				difference = new_diff;
				energy_index = i;
			}
		}
	}

	// search CDF for angle
	double u = common::get_rand();
	int k = 0;
	while (diff_sigma_CDFs[part_index][energy_index][0][k] < u)
	{
		k++;
	}
	return diff_sigma_CDFs[part_index][energy_index][1][k];
}

// get density from imported density profile
double Background_Species::get_density(double alt, int index)
{
	double current_dens = 0.0;

	// if outside of profile boundaries, need to extrapolate using a scale height
	if (alt < profile_bottom_alt)
	{
		current_dens = calc_new_density(bg_densities[index][0], bg_scaleheights[index][0], profile_bottom_alt - alt);
	}
	else if (alt > profile_top_alt)
	{
		current_dens = calc_new_density(bg_densities[index].back(), bg_scaleheights[index][1], profile_top_alt - alt);
	}
	else
	{
		current_dens = dens_interp[index]->loglinterp(alt);
	}

	return current_dens;
}

int Background_Species::get_num_collisions()
{
	return num_collisions;
}

shared_ptr<Particle> Background_Species::get_collision_target()
{
	return bg_parts[collision_target];
}

double Background_Species::get_collision_theta()
{
	return collision_theta;
}

double Background_Species::get_collision_dE()
{
	return collision_dE;
}

// reads every comma-separated numeric column of a csv file ('#' and blank lines skipped); cols[0] is the first column
void Background_Species::read_columns(string filename, vector<vector<double>> &cols)
{
	ifstream infile;
	infile.open(filename);
	if (!infile.good())
	{
		cout << "\"" << filename << "\" not found!\n";
		exit(1);
	}
	string line, word;
	while (getline(infile, line))
	{
		if (line[0] == '#' || line.empty() || std::all_of(line.begin(), line.end(), ::isspace))
		{
			continue;
		}
		vector<string> row;
		stringstream str(line);
		while (getline(str, word, ','))
		{
			row.push_back(word);
		}
		if (cols.empty())
		{
			cols.resize(row.size());
		}
		if (row.size() != cols.size())
		{
			cout << "\"" << filename << "\": rows with different numbers of columns!\n";
			exit(1);
		}
		for (size_t c=0; c<row.size(); c++)
		{
			cols[c].push_back(stod(row[c]));
		}
	}
	infile.close();
}

// reads the channel table: a row 'dE_eV,<energy loss (eV) of each channel>' and then rows 'E_eV,<cross section (cm^2) of each channel>'
void Background_Species::read_channel_file(string filename, int n, int part_index)
{
	ifstream infile;
	infile.open(filename);
	if (!infile.good())
	{
		cout << "\"" << filename << "\" not found!\n";
		exit(1);
	}
	channel_dE[part_index].clear();
	channel_E[part_index].clear();
	channel_sigma[part_index].assign(n, vector<double>());
	bool have_dE = false;
	string line, word;
	while (getline(infile, line))
	{
		if (line[0] == '#' || line.empty() || std::all_of(line.begin(), line.end(), ::isspace))
		{
			continue;
		}
		vector<string> row;
		stringstream str(line);
		while (getline(str, word, ','))
		{
			row.push_back(word);
		}
		if ((int)row.size() != n + 1)
		{
			cout << "\"" << filename << "\": rows must have 1 + num_channels values!\n";
			exit(1);
		}
		if (row[0] == "dE_eV")
		{
			for (int c=0; c<n; c++)
			{
				channel_dE[part_index].push_back(stod(row[c+1]));
			}
			have_dE = true;
		}
		else
		{
			channel_E[part_index].push_back(stod(row[0]));
			for (int c=0; c<n; c++)
			{
				channel_sigma[part_index][c].push_back(stod(row[c+1]));
			}
		}
	}
	infile.close();
	if (!have_dE || channel_E[part_index].size() < 2)
	{
		cout << "\"" << filename << "\": needs a 'dE_eV' row and at least two energy rows!\n";
		exit(1);
	}
}

// chooses the channel of a collision at this collision energy (eV): probability proportional to the channel cross section
// (interpolated linearly in energy, end values outside the table), closed channels (energy loss >= collision energy) excluded
int Background_Species::pick_channel(int part_index, double energy)
{
	int n = num_channels[part_index];
	if (n == 1)
	{
		return 0;   // single channel: nothing to choose, and no random number is used
	}
	const vector<double> &E = channel_E[part_index];
	int i_lo = 0, i_hi = 0;
	double w_hi = 0.0;
	if (energy <= E.front())
	{
		i_lo = i_hi = 0;
	}
	else if (energy >= E.back())
	{
		i_lo = i_hi = (int)E.size() - 1;
	}
	else
	{
		i_hi = lower_bound(E.begin(), E.end(), energy) - E.begin();
		i_lo = i_hi - 1;
		w_hi = (energy - E[i_lo]) / (E[i_hi] - E[i_lo]);
	}
	vector<double> w(n, 0.0);
	double total = 0.0;
	for (int c=0; c<n; c++)
	{
		if (channel_dE[part_index][c] >= energy)
		{
			continue;   // channel closed at this collision energy
		}
		w[c] = (1.0 - w_hi)*channel_sigma[part_index][c][i_lo] + w_hi*channel_sigma[part_index][c][i_hi];
		total += w[c];
	}
	if (total <= 0.0)
	{
		return 0;   // nothing open: elastic
	}
	double u = common::get_rand() * total;
	double cum = 0.0;
	int last = 0;
	for (int c=0; c<n; c++)
	{
		if (w[c] > 0.0)
		{
			last = c;
			cum += w[c];
			if (u < cum)
			{
				return c;
			}
		}
	}
	return last;   // rounding: the last open channel
}

// scans the angle CDF of one channel (at the tabulated energy nearest to the collision energy) for a new collision theta
double Background_Species::find_new_theta_channel(int part_index, int channel, double energy)
{
	int energy_index = 0;
	int num_energies = diff_sigma_energies[part_index].size();
	if (energy <= diff_sigma_energies[part_index][0])
	{
		energy_index = 0;
	}
	else if (energy >= diff_sigma_energies[part_index].back())
	{
		energy_index = num_energies - 1;
	}
	else
	{
		double difference = INFINITY;
		for (int i=0; i<num_energies; i++)
		{
			double new_diff = abs(energy - diff_sigma_energies[part_index][i]);
			if (new_diff < difference)
			{
				difference = new_diff;
				energy_index = i;
			}
		}
	}
	const vector<double> &cdf = channel_CDFs[part_index][energy_index][channel][0];
	const vector<double> &ang = channel_CDFs[part_index][energy_index][channel][1];
	double u = common::get_rand();
	int k = 0;
	int last = (int)cdf.size() - 1;
	while (cdf[k] < u && k < last)
	{
		k++;
	}
	return ang[k];
}

// builds the angle CDF of one channel (same method as make_new_CDF)
void Background_Species::make_channel_CDF(int part_index, int energy_index, int channel, vector<double> angle, vector<double> sigma)
{
	int num_angles = angle.size();
	channel_CDFs[part_index][energy_index][channel].resize(2);
	vector<double> &cdf = channel_CDFs[part_index][energy_index][channel][0];
	vector<double> &ang = channel_CDFs[part_index][energy_index][channel][1];
	cdf.resize(num_angles);
	ang.resize(num_angles);
	double sig_total = 0.0;
	for (int i=0; i<num_angles; i++)
	{
		ang[i] = angle[i] * (constants::pi / 180.0);
		sigma[i] = sigma[i] * sin(angle[i]*constants::pi/180.0);
		sig_total = sig_total + sigma[i];
	}
	if (!(sig_total > 0.0))
	{
		cout << "Angle distribution of channel " << channel+1 << " has no positive values: check the channel angle file!\n";
		exit(1);
	}
	for (int i=0; i<num_angles; i++)
	{
		cdf[i] = sigma[i] / sig_total + (i > 0 ? cdf[i-1] : 0.0);
	}
}

void Background_Species::print_channel_stats()
{
	for (int i=0; i<num_species; i++)
	{
		if (num_channels[i] == 0)
		{
			continue;
		}
		long n = 0;
		for (int c=0; c<num_channels[i]; c++)
		{
			n += channel_counts[i][c];
		}
		cout << "Channel statistics for " << bg_parts[i]->get_name() << ": " << n << " collisions";
		if (n > 0)
		{
			cout << ", fraction in channel 1 (elastic) " << (double)channel_counts[i][0] / (double)n << ", mean energy loss per collision (eV) " << channel_dE_sum[i] / (double)n;
		}
		cout << endl;
		cout << "Collisions per channel (channel 1 first):";
		for (int c=0; c<num_channels[i]; c++)
		{
			cout << " " << channel_counts[i][c];
		}
		cout << endl;
	}
}

// make a new differential cross section CDF and store at diff_sigma_CDFs[part_index][energy_index]
void Background_Species::make_new_CDF(int part_index, int energy_index, vector<double> &angle, vector<double> &sigma)
{
	int num_angles = angle.size();
	diff_sigma_CDFs[part_index][energy_index][0].resize(num_angles);
	diff_sigma_CDFs[part_index][energy_index][1].resize(num_angles);

	double sig_total = 0.0;
	for (int i=0; i<num_angles; i++)
	{
		diff_sigma_CDFs[part_index][energy_index][1][i] = angle[i] * (constants::pi / 180.0);
		sigma[i] = sigma[i] * sin(angle[i]*constants::pi/180.0);
		sig_total = sig_total + sigma[i];
	}
	for (int i=0; i<num_angles; i++)
	{
		if (i == 0)
		{
			diff_sigma_CDFs[part_index][energy_index][0][i] = sigma[i] / sig_total;
		}
		else
		{
			diff_sigma_CDFs[part_index][energy_index][0][i] = (sigma[i] / sig_total) + diff_sigma_CDFs[part_index][energy_index][0][i-1];
		}
	}
}

//subroutine to set particle types
shared_ptr<Particle> Background_Species::set_particle_type(string type)
{
	shared_ptr<Particle> p;

	if (type == "H")
	{
		p = make_shared<Particle_H>();
	}
	else if (type == "O")
	{
		p = make_shared<Particle_O>();
	}
	else if (type == "N2")
	{
		p = make_shared<Particle_N2>();
	}
	else if (type == "CO")
	{
		p = make_shared<Particle_CO>();
	}
	else if (type == "CO2")
	{
		p = make_shared<Particle_CO2>();
	}
	else
	{
		cout << "Invalid particle type specified! Please check configuration file.\n";
		exit(1);
	}
	return p;
}
