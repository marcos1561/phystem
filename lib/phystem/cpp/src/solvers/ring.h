#include <cmath>
#include <vector>
#include <array>
#include <iostream>
#include <cstdlib> 

#include "../configs/ring.h"
#include "../rng_manager.h"
#include "../windows_manager.h"
#include "../macros_defs.h"

#include "../intersections.h"

using Vec2d = std::array<double, 2>;
using Vector2d = std::vector<std::array<double, 2>>;
using Vector3d = std::vector<std::vector<std::array<double, 2>>>;

double dot_prod(Vec2d &a, Vec2d& b) {
    return a[0] * b[0] + a[1] * b[1];
}

double cross_prod(Vec2d &a, Vec2d& b) {
    return a[0] * b[1] - a[1] * b[0];
}

double vector_dist(Vec2d& a, Vec2d& b) {
    double dx = b[0] - a[0];
    double dy = b[1] - a[1];
    double comp = sqrt(dx*dx + dy*dy);

    return comp;
}

double vector_mod(Vec2d& a) {
    return sqrt(a[0]*a[0] + a[1]*a[1]);
}

struct SpringDebug {
    int count_overlap;
};

struct ExcludedVolDebug {
    int count_overlap;
};

struct AreaDebug {
    int count_overlap;

    vector<double> area;
};

struct UpdateDebug {
    int count_zero_speed;
};

class Ring {
public:
    double spring_k;
    double spring_r;

    double k_bend;
    double p0;
    double area0;
    double p_target;

    double mobility;
    double relax_time;
    double vo;

    double trans_diff;
    double rot_diff;

    double exclusion_vol;
    double diameter; 
    double diameter_six; 
    double diameter_twelve; 

    double force_r_lim;

    Vector3d pos; // Posições das partículas
    Vector3d vel; // Velocidades das partículas (Utilizado pelo verlet)
    vector<vector<double>> self_prop_angle; // Ângulo da direção da velocidade auto propulsora
    vector<vector<double>> self_prop_angle_deriv; // Derivada do ângulo da direção da velocidade auto propulsora. (Utilizado pelo verlet)
    
    Vector3d old_pos; // Posições das partículas
    vector<vector<double>> old_self_prop_angle; // Ângulo da direção da velocidade auto propulsora

    RingCfg dynamic_cfg; // Configurações da dinâmica entre as partículas
    double size; // tamanho de uma dimensão do espaço
    double dt; 
    int windows_update_freq; 
    int integration_type;

    double sim_time;
    int num_time_steps;

    int num_particles; // Número de partículas no anel
    int num_rings; 
    
    Vector3d sum_forces_matrix; // Matrix com a soma das forças sobre cada partícula

    WindowsManagerRing windows_manager;

    //==
    // Area Potencial
    //==
    Vector3d differences; // Vetor cujo i-ésimo elemento contém pos[i+1] - pos[i]
    Vector3d pos_continuos; // Posições das partículas de forma contínua
    //=========//


    //==
    // DEBUG
    //==
    Vector3d total_forces;
    Vector3d spring_forces;
    Vector3d vol_forces;
    Vector3d area_forces;

    vector<vector<vector<double*>>> pos_t; // Transposta da posições das partículas
    
    // Pontos utilizados na renderização do anel, sua estrutura é a seguinte
    //
    // [p1, pm1_1, pm1_2, p2, pm2_1, pm2_2, p3, pm3_1, pm3_2, p4, ...]
    //
    // Em que p{i} é o i-ésimo ponto no anel e pm{i}_{1, 2} são os pontos médios entre
    // o i-ésimo e (i+1)-ésimo ponto do anel.
    Vector3d graph_points;

    RngManager rng_manager;
    IntersectionCalculator intersect;

    UpdateDebug update_debug = {0};
    SpringDebug spring_debug = {0};
    ExcludedVolDebug excluded_vol_debug = {0};
    AreaDebug area_debug = {0};
    //=========//

    Ring(Vector3d &pos0, vector<vector<double>> self_prop_angle0, RingCfg dynamic_cfg, 
        double size, double dt, int num_col_windows, int seed=-1, int windows_update_freq=1,
        int integration_type=0) 
    : pos(pos0), self_prop_angle(self_prop_angle0), dynamic_cfg(dynamic_cfg), size(size), dt(dt),
    windows_update_freq(windows_update_freq), integration_type(integration_type)
    {
        if (seed != -1.)
            srand(seed);
        else
            srand(time(0));

        std::cout << "Update freq: " << windows_update_freq << std::endl;

        num_particles = pos0[0].size();
        num_rings = pos0.size();
        sim_time = 0.0;
        num_time_steps = 0;

        windows_manager = WindowsManagerRing(&pos, num_col_windows, num_col_windows, size, windows_update_freq);

        initialize_dynamic();
        
        #if DEBUG == 1
        rng_manager = RngManager(num_particles, num_rings, 3);
        intersect = IntersectionCalculator(size);
        #endif
    }

    void initialize_dynamic() {
        spring_k = dynamic_cfg.spring_k;
        spring_r = dynamic_cfg.spring_r;
        
        k_bend = dynamic_cfg.k_bend;
        p0 = dynamic_cfg.p0;
        area0 = dynamic_cfg.area0;
        p_target = p0 * sqrt(area0);

        // area0 = calc_area(pos[0]);

        mobility = dynamic_cfg.mobility;
        relax_time = dynamic_cfg.relax_time;
        vo = dynamic_cfg.vo;

        trans_diff = dynamic_cfg.trans_diff;
        rot_diff = dynamic_cfg.rot_diff;

        exclusion_vol = dynamic_cfg.exclusion_vol;
        diameter = dynamic_cfg.diameter;

        diameter_six = pow(diameter, 6.); 
        diameter_twelve = pow(diameter, 12.); 
        force_r_lim = pow(2, 1./6.) * diameter;

        auto zero_vector_1d = vector<double>(num_particles, 0.); 
        auto zero_vector_2d = vector<array<double, 2>>(num_particles, {0., 0.}); 

        old_pos = Vector3d(num_rings, zero_vector_2d);
        vel = Vector3d(num_rings, zero_vector_2d);
        old_self_prop_angle = vector<vector<double>>(num_rings, zero_vector_1d);
        self_prop_angle_deriv = vector<vector<double>>(num_rings, zero_vector_1d);
        
        sum_forces_matrix = Vector3d(num_rings, zero_vector_2d);
        
        differences = Vector3d(num_rings, zero_vector_2d);
        pos_continuos = Vector3d(num_rings, zero_vector_2d);

        #if DEBUG == 1
        // for (int i = 0; i < num_skip_steps; i++)
        // {
        //     rng_manager.update();
        // }

        spring_forces = Vector3d(num_rings, zero_vector_2d);
        vol_forces = Vector3d(num_rings, zero_vector_2d);
        area_forces = Vector3d(num_rings, zero_vector_2d);
        total_forces = Vector3d(num_rings, zero_vector_2d);

        area_debug.area = vector<double>(num_rings);

        // vector<vector<double*>> ring_pos_t;
        pos_t = vector<vector<vector<double*>>>(num_rings, vector<vector<double*>>(2));
        for (int i=0; i < num_rings; i ++) {
            for (int j = 0; j < num_particles; j++)
            {
                pos_t[i][0].push_back(&pos[i][j][0]);
                pos_t[i][1].push_back(&pos[i][j][1]);
            }
        }

        graph_points = Vector3d(num_rings, vector<array<double, 2>>(3*num_particles, {0., 0.}));
        
        update_graph_points();
        #endif
    }

    double periodic_dist(double &dx, double &dy) {
        /**
         * Retorna a distância, considerando as bordas periódicas, para a 
         * diferença entre dois pontos (sem considerar as bordas periódicas) dados por "dx" e "dy".
         * 
         * OBS: Esse método atualiza 'dx' e 'dy' para ficarem de acordo com as bordas periódicas.
         * 
         * NOTE: Quando o espaço não for um quadrado, é necessário
         * usar box_width para o dx e box_height para o dy.       
        */
        if (abs(dx) > size * 0.5)
            dx -= copysign(size, dx);

        if (abs(dy) > size * 0.5)
            dy -= copysign(size, dy);

        return sqrt(dx*dx + dy*dy);
    }
 
    void calc_forces_normal(int ring_id) {
        // Excluded volume
        for (int p_id = 0; p_id < num_particles; p_id ++) {
            for (int other_ring_id = 0; other_ring_id < num_rings; other_ring_id++)
            {
                if (other_ring_id == ring_id) {
                    for (int other_id = 0; other_id < num_particles; other_id ++) {
                        if (other_id == p_id) {
                            continue;
                        }
                        calc_excluded_vol_force(ring_id, ring_id, p_id, other_id);
                    }
                } else {
                    for (int other_id = 0; other_id < num_particles; other_id++)
                    {
                        calc_excluded_vol_force(ring_id, other_ring_id, p_id, other_id);
                    }
                }
            }
        }

        // Springs
        for (int p_id = 0; p_id < num_particles; p_id ++) {
            int id_left = (p_id == 0) ? num_particles-1 : p_id-1;
            int id_right = (p_id == num_particles-1) ? 0 : p_id+1;

            calc_spring_force(ring_id, p_id, id_left);
            calc_spring_force(ring_id, p_id, id_right);
        }

        // Bend
        switch (dynamic_cfg.area_potencial)
        {
        case AreaPotencialType::format:
            format_forces(ring_id);
            break;
        case AreaPotencialType::target_perimeter:
            target_perimeter_forces(ring_id);
            break;
        case AreaPotencialType::target_area:
            target_area_forces(ring_id);
            break;
        }
    }

    void calc_excluded_vol_force(int ring_id, int other_ring_id, int p_id, int other_id, bool use_third_law=false) {
        /**
         * Calcula a força do potencial de volume exercida na partícula 'p_id' no anel 'ring_id', 
         * pela partícula 'other_id' que está no anel 'other_ring_id'.
         * 
         * OBS: A força calculada é somada em 'sum_forces_matrix', e caso esteja no modo
         * DEBUG, a forma também é somada em 'vol_forces'.
        */

        auto &p = pos[ring_id][p_id];
        auto &other = pos[other_ring_id][other_id];

        double dx = p[0] - other[0];
        double dy = p[1] - other[1];

        double dist = periodic_dist(dx, dy);

        if (dist > force_r_lim) { 
            return; 
        } 

        #if DEBUG == 1                
        if (dist == 0.) {
            excluded_vol_debug.count_overlap += 1;
        }
        #endif

        double force_intensity = exclusion_vol * (0.5 * diameter_six / pow(dist, 7.) - diameter_twelve/pow(dist, 13.) );
        force_intensity = abs(force_intensity);

        double vol_fx = force_intensity/dist * dx;
        double vol_fy = force_intensity/dist * dy;

        sum_forces_matrix[ring_id][p_id][0] += vol_fx;
        sum_forces_matrix[ring_id][p_id][1] += vol_fy;
        
        if (use_third_law) {
            sum_forces_matrix[other_ring_id][other_id][0] -= vol_fx;
            sum_forces_matrix[other_ring_id][other_id][1] -= vol_fy;
        }

        #if DEBUG == 1
        vol_forces[ring_id][p_id][0] += vol_fx;
        vol_forces[ring_id][p_id][1] += vol_fy;
        
        if (use_third_law) {
            vol_forces[other_ring_id][other_id][0] -= vol_fx;
            vol_forces[other_ring_id][other_id][1] -= vol_fy;
        }
        #endif
    }

    void calc_spring_force(int ring_id, int p_id, int other_id) {
        auto& p = pos[ring_id][p_id]; 
        auto& other = pos[ring_id][other_id]; 

        double dx = other[0] - p[0];         
        double dy = other[1] - p[1];

        double dist = periodic_dist(dx, dy);

        #if DEBUG == 1                
        if (dist == 0.) {
            spring_debug.count_overlap += 1;
        }
        #endif

        double force_intensity = spring_k * (dist - spring_r);         

        double spring_fx = dx/dist * force_intensity;
        double spring_fy = dy/dist * force_intensity;

        sum_forces_matrix[ring_id][p_id][0] += spring_fx;
        sum_forces_matrix[ring_id][p_id][1] += spring_fy;

        #if DEBUG == 1
        spring_forces[ring_id][p_id][0] += spring_fx;
        spring_forces[ring_id][p_id][1] += spring_fy;
        #endif
    }


    double calc_differences(int ring_id) {
        double perimeter = 0;

        double dx, dy;
        for (int i = 0; i < (num_particles-1); i++)
        {
            dx = pos[ring_id][i+1][0] - pos[ring_id][i][0];
            dy = pos[ring_id][i+1][1] - pos[ring_id][i][1];
            perimeter += periodic_dist(dx, dy);
            
            differences[ring_id][i] = {dx, dy};
        }

        dx = pos[ring_id][0][0] - pos[ring_id][num_particles-1][0];
        dy = pos[ring_id][0][1] - pos[ring_id][num_particles-1][1];
        perimeter += periodic_dist(dx, dy);

        differences[ring_id][num_particles-1] = {dx, dy}; 

        return perimeter;
    }

    double calc_area(Vector2d& points) const {
        double area = 0.0;

        for (size_t i = 0; i < points.size()-1; i++) {
            auto& p1 = points[i];
            auto& p2 = points[i+1];
            area += cross_prod(p1, p2);
        }
        int i = points.size() - 1;
        auto& p1 = points[i];
        auto& p2 = points[0];
        area += cross_prod(p1, p2);

        return area / 2.0;
    }

    double calc_perimeter(Vector2d& points) const {
        double perimeter = 0.0;

        for (size_t i = 0; i < points.size()-1; i++)
        {
            perimeter += vector_dist(points[i], points[i+1]);
        }
        int i = points.size() - 1;
        perimeter += vector_dist(points[i], points[0]);

        return perimeter;
    }

    void format_force(int ring_id, int point_id, double area, double perimeter) {
        int id = pos_continuos[ring_id].size() - 1;
        if (point_id != 0)
            id = point_id - 1;
        auto& v1 = pos_continuos[ring_id][id];
        
        id = 0;
        if (point_id != (pos_continuos[ring_id].size() - 1))
            id = point_id + 1;
        auto& v2 = pos_continuos[ring_id][id];

        auto& point = pos_continuos[ring_id][point_id]; 

        double d1 = vector_dist(v1, pos_continuos[ring_id][point_id]);
        double d2 = vector_dist(v2, pos_continuos[ring_id][point_id]);

        #if DEBUG == 1                
        if (d1 == 0.)
            area_debug.count_overlap += 1;
        if (d2 == 0.) 
            area_debug.count_overlap += 1;
        #endif

        double delta_area = area - (perimeter/p0) * (perimeter/p0);

        double area_0_deriv_x =  2.0 * perimeter / (p0*p0) * ((v1[0] - point[0]) / d1 +  (v2[0] - point[0]) / d2);
        double area_0_deriv_y =  2.0 * perimeter / (p0*p0) * ((v1[1] - point[1]) / d1 +  (v2[1] - point[1]) / d2);
        
        double gradient_x = k_bend * delta_area * ((v2[1] - v1[1])/2.0 + area_0_deriv_x);
        double gradient_y = k_bend * delta_area * (-(v2[0] - v1[0])/2.0 + area_0_deriv_y);

        #if DEBUG == 1
        area_forces[ring_id][point_id][0] = -gradient_x;
        area_forces[ring_id][point_id][1] = -gradient_y;
        #endif

        sum_forces_matrix[ring_id][point_id][0] -= gradient_x;
        sum_forces_matrix[ring_id][point_id][1] -= gradient_y;
    }

    void format_forces(int ring_id) {
        double perimeter = calc_differences(ring_id);

        pos_continuos[ring_id][0] = pos[ring_id][0];
        for (size_t i = 0; i < (differences[ring_id].size()-1); i++)
        {
            pos_continuos[ring_id][i+1][0] = pos_continuos[ring_id][i][0] + differences[ring_id][i][0];
            pos_continuos[ring_id][i+1][1] = pos_continuos[ring_id][i][1] + differences[ring_id][i][1];
        }

        double area = calc_area(pos_continuos[ring_id]);
        
        #if DEBUG
        area_debug.area[ring_id] = area;
        #endif

        for (size_t i = 0; i < pos_continuos[ring_id].size(); i++)
        {
            format_force(ring_id, i, area, perimeter);
        }
    }

    void target_perimeter_forces(int ring_id) {
        double perimeter = calc_differences(ring_id);

        pos_continuos[ring_id][0] = pos[ring_id][0];
        for (size_t i = 0; i < (differences[ring_id].size()-1); i++)
        {
            pos_continuos[ring_id][i+1][0] = pos_continuos[ring_id][i][0] + differences[ring_id][i][0];
            pos_continuos[ring_id][i+1][1] = pos_continuos[ring_id][i][1] + differences[ring_id][i][1];
        }

        double area = calc_area(pos_continuos[ring_id]);
        #if DEBUG
        area_debug.area[ring_id] = area;
        #endif

        auto& ring_pos = pos[ring_id];
        for (int i = 0; i < num_particles; i++)
        {
            double d1 = vector_mod(differences[ring_id][i]);
            
            int id2 = i-1;
            if (i == 0)
                id2 = num_particles - 1;
            double d2 = vector_mod(differences[ring_id][id2]);
            
            double  force_k = k_bend * (perimeter - p_target);

            // int id1 = i - 1;
            // if (id1 == -1)
            //     id1 = num_particles - 1;

            // id2 = i;

            // int id3 = i + 1;
            // if (id3 == num_particles)
            //     id3 = 0;

            // double p_deriv_x = (ring_pos[id2][0] - ring_pos[id1][0])/d1 + (ring_pos[id2][0] - ring_pos[id3][0])/d2;
            // double p_deriv_y = (ring_pos[id2][1] - ring_pos[id1][1])/d1 + (ring_pos[id2][1] - ring_pos[id3][1])/d2;



            double p_deriv_x = (-differences[ring_id][i][0])/d1 + (differences[ring_id][id2][0])/d2;
            double p_deriv_y = (-differences[ring_id][i][1])/d1 + (differences[ring_id][id2][1])/d2;
            
            double fx = -force_k * p_deriv_x;
            double fy = -force_k * p_deriv_y;

            #if DEBUG == 1
            area_forces[ring_id][i][0] = fx;
            area_forces[ring_id][i][1] = fy;
            #endif


            sum_forces_matrix[ring_id][i][0] += fx;
            sum_forces_matrix[ring_id][i][1] += fy;
        }
    }

    void target_area_forces(int ring_id) {
        double perimeter = calc_differences(ring_id);

        pos_continuos[ring_id][0] = pos[ring_id][0];
        for (size_t i = 0; i < (differences[ring_id].size()-1); i++)
        {
            pos_continuos[ring_id][i+1][0] = pos_continuos[ring_id][i][0] + differences[ring_id][i][0];
            pos_continuos[ring_id][i+1][1] = pos_continuos[ring_id][i][1] + differences[ring_id][i][1];
        }

        double area = calc_area(pos_continuos[ring_id]);
        #if DEBUG
        area_debug.area[ring_id] = area;
        #endif

        auto& ring_pos = pos[ring_id];
        int id1, id2;
        for (int i = 0; i < num_particles; i++)
        {
            double force_k = k_bend * (area - area0);

            id1 = i - 1;
            if (id1 == -1)
                id1 = num_particles - 1;
            
            id2 = i + 1;
            if (id2 == num_particles)
                id2 = 0;

            
            double dx = ring_pos[id2][0] - ring_pos[id1][0];
            double dy = ring_pos[id2][1] - ring_pos[id1][1];
            periodic_dist(dx, dy);

            double a_deriv_x = 1.0/2.0 * (dy);
            double a_deriv_y = 1.0/2.0 * (-dx);
            
            double fx = -force_k * a_deriv_x;
            double fy = -force_k * a_deriv_y;

            #if DEBUG == 1
            area_forces[ring_id][i][0] = fx;
            area_forces[ring_id][i][1] = fy;
            #endif


            sum_forces_matrix[ring_id][i][0] += fx;
            sum_forces_matrix[ring_id][i][1] += fy;
        }
    }

    void calc_derivate(Vec2d &vel_i, double &angle_deriv_i, int ring_id, int particle_id) {
        int i = particle_id;
        Vec2d self_vel_i = {cos(self_prop_angle[ring_id][i]), sin(self_prop_angle[ring_id][i])};

        #if DEBUG == 1    
            auto& rng_nums = rng_manager.get_random_num(i, ring_id);
            double rng_rot = (double)rng_nums[0]/(double)RAND_MAX * 2. - 1.;
            double rng_trans_x = (double)rng_nums[1]/(double)RAND_MAX * 2. - 1.;
            double rng_trans_y = (double)rng_nums[2]/(double)RAND_MAX * 2. - 1.;
        #else
            double rng_rot = (double)rand()/(double)RAND_MAX * 2. - 1.;
            double rng_trans_x = (double)rand()/(double)RAND_MAX * 2. - 1.;
            double rng_trans_y = (double)rand()/(double)RAND_MAX * 2. - 1.;
        #endif
        double noise_rot = rng_rot * sqrt(2. * rot_diff) / sqrt(dt); 
        double noise_trans_x = rng_trans_x * sqrt(2. * trans_diff) / sqrt(dt); 
        double noise_trans_y = rng_trans_y * sqrt(2. * trans_diff) / sqrt(dt); 
        
        double vel_x_i = vo * self_vel_i[0] + mobility * sum_forces_matrix[ring_id][i][0] + noise_trans_x;
        double vel_y_i = vo * self_vel_i[1] + mobility * sum_forces_matrix[ring_id][i][1] + noise_trans_y;

        double speed = sqrt(vel_x_i*vel_x_i + vel_y_i * vel_y_i);

        #if DEBUG == 1
        if (speed > 1e6) {
            std::cout << "Error: High velocity" << std::endl;
        }
        #endif
        
        double angle_derivate;
        if (speed == 0.) {
            update_debug.count_zero_speed += 1;
            angle_derivate = 0.;
        } else {
            double cross_prod = self_vel_i[0] * vel_y_i/speed - self_vel_i[1] * vel_x_i/speed;
            
            if (abs(cross_prod) > 1) {
                #if DEBUG == 1
                std::cout << "Error: cross_prod | " << cross_prod << std::endl;
                #endif
                cross_prod = copysign(1, cross_prod);
            }

            angle_derivate = 1. / relax_time * asin(cross_prod) + noise_rot;
        }

        vel_i[0] = vel_x_i;
        vel_i[1] = vel_y_i;
        angle_deriv_i = angle_derivate;
    }

    void advance_time(int ring_id) {
        double angle_deriv_i;
        Vec2d vel_i;

        for (int i=0; i < num_particles; i++) {
            calc_derivate(vel_i, angle_deriv_i, ring_id, i);

            pos[ring_id][i][0] += vel_i[0] * dt;
            pos[ring_id][i][1] += vel_i[1] * dt;
            self_prop_angle[ring_id][i] += angle_deriv_i * dt;

            if (isnan(pos[ring_id][i][0]) == true) {
                std::cout << "Error: pos nan 1" << std::endl;
            }

            for (int dim = 0; dim < 2.f; dim ++) {
                if (pos[ring_id][i][dim] > size/2.f)
                    pos[ring_id][i][dim] -= size;
                else if (pos[ring_id][i][dim] < -size/2.f)
                    pos[ring_id][i][dim] += size;
            }

            #if DEBUG == 1
            if (isnan(pos[ring_id][i][0]) == true)
                std::cout << "Error: pos_nan 2" << std::endl;

            total_forces[ring_id][i][0] = sum_forces_matrix[ring_id][i][0];
            total_forces[ring_id][i][1] = sum_forces_matrix[ring_id][i][1];
            #endif

            sum_forces_matrix[ring_id][i][0] = 0.f;
            sum_forces_matrix[ring_id][i][1] = 0.f;
        }        
    }

    void advance_time_verlet() {
        for (int ring_id = 0; ring_id < num_rings; ring_id++)
        {
            for (int i=0; i < num_particles; i++) {
                auto& vel_i = vel[ring_id][i];
                auto& angle_deriv_i = self_prop_angle_deriv[ring_id][i];

                #if DEBUG == 1
                if (isnan(vel_i[0]) == true) {
                    std::cout << "Error: vel nan 1" << std::endl;
                }
                #endif
                
                calc_derivate(vel_i, angle_deriv_i, ring_id, i);

                #if DEBUG == 1
                if (isnan(vel_i[0]) == true) {
                    std::cout << "Error: vel nan 2" << std::endl;
                }
                #endif

                old_pos[ring_id][i][0] = pos[ring_id][i][0];
                old_pos[ring_id][i][1] = pos[ring_id][i][1];
                old_self_prop_angle[ring_id][i] = self_prop_angle[ring_id][i];
                
                pos[ring_id][i][0] += vel_i[0] * dt;
                pos[ring_id][i][1] += vel_i[1] * dt;
                self_prop_angle[ring_id][i] += angle_deriv_i * dt;

                #if DEBUG == 1
                if (isnan(pos[ring_id][i][0]) == true) {
                    std::cout << "Error: pos nan 1" << std::endl;
                }
                #endif

                for (int dim = 0; dim < 2.f; dim ++) {
                    if (pos[ring_id][i][dim] > size/2.f)
                        pos[ring_id][i][dim] -= size;
                    else if (pos[ring_id][i][dim] < -size/2.f)
                        pos[ring_id][i][dim] += size;
                }

                #if DEBUG == 1
                if (isnan(pos[ring_id][i][0]) == true)
                    std::cout << "Error: pos_nan 2" << std::endl;
                #endif

                sum_forces_matrix[ring_id][i][0] = 0.f;
                sum_forces_matrix[ring_id][i][1] = 0.f;
            } 
        }
        
        calc_forces_windows();

        double angle_deriv_i;
        Vec2d vel_i;
        for (int ring_id = 0; ring_id < num_rings; ring_id++)
        {
            for (int i=0; i < num_particles; i++) {
                calc_derivate(vel_i, angle_deriv_i, ring_id, i);

                auto& old_pos_i = old_pos[ring_id][i];
                auto& vel1 = vel[ring_id][i];

                pos[ring_id][i][0] = old_pos_i[0] + 0.5 * (vel1[0] + vel_i[0]) * dt;
                pos[ring_id][i][1] = old_pos_i[1] + 0.5 * (vel1[1] + vel_i[1]) * dt;
                self_prop_angle[ring_id][i] = old_self_prop_angle[ring_id][i] + 0.5 * (self_prop_angle_deriv[ring_id][i] + angle_deriv_i) * dt;

                if (isnan(pos[ring_id][i][0]) == true) {
                    std::cout << "Error: pos nan 1" << std::endl;
                }

                for (int dim = 0; dim < 2.f; dim ++) {
                    if (pos[ring_id][i][dim] > size/2.f)
                        pos[ring_id][i][dim] -= size;
                    else if (pos[ring_id][i][dim] < -size/2.f)
                        pos[ring_id][i][dim] += size;
                }

                #if DEBUG == 1
                if (isnan(pos[ring_id][i][0]) == true)
                    std::cout << "Error: pos_nan 2" << std::endl;

                total_forces[ring_id][i][0] = sum_forces_matrix[ring_id][i][0];
                total_forces[ring_id][i][1] = sum_forces_matrix[ring_id][i][1];
                #endif

                sum_forces_matrix[ring_id][i][0] = 0.f;
                sum_forces_matrix[ring_id][i][1] = 0.f;
            }
        }
    }

    void update_normal() {
        #if DEBUG == 1
        rng_manager.update();
        #endif

        for (int ring_id = 0; ring_id < num_rings; ring_id++) {
            #if DEBUG == 1
            for (int i = 0; i < num_particles; i++) {
                spring_forces[ring_id][i][0] = 0.;
                spring_forces[ring_id][i][1] = 0.;
                
                vol_forces[ring_id][i][0] = 0.;
                vol_forces[ring_id][i][1] = 0.;
            }
            #endif

            calc_forces_normal(ring_id);
        }

        switch (integration_type)
        {
        case 0:
            for (int ring_id = 0; ring_id < num_rings; ring_id++) {
                advance_time(ring_id);
            }
            break;
        case 1:
            advance_time_verlet();
            break;
        }
        
        
        #if DEBUG == 1
        update_graph_points();   
        #endif

        sim_time += dt;
        num_time_steps += 1;
    }
   
    void calc_forces_windows() {
        #if DEBUG == 1
        for (int ring_id = 0; ring_id < num_rings; ring_id++) {
            for (int i = 0; i < num_particles; i++) {
                spring_forces[ring_id][i][0] = 0.;
                spring_forces[ring_id][i][1] = 0.;
                
                vol_forces[ring_id][i][0] = 0.;
                vol_forces[ring_id][i][1] = 0.;
            }
        }
        #endif

        // Excluded volume
        for (auto win_id: windows_manager.windows_ids) {
            auto & window = windows_manager.windows[win_id[0]][win_id[1]];
            auto & neighbors = windows_manager.window_neighbor[win_id[0]][win_id[1]];
            int windows_cap = windows_manager.capacity[win_id[0]][win_id[1]];
            
            for (int i=0; i < windows_cap; i++) {
                auto ring_id = window[i][0];
                auto p_id = window[i][1];

                for (int j = i+1; j < windows_cap; j ++) {
                    auto other_id = window[j];
                    calc_excluded_vol_force(ring_id, other_id[0], p_id, other_id[1], true);
                }

                for (auto neigh_id : neighbors) {
                    auto & neigh_window = windows_manager.windows[neigh_id[0]][neigh_id[1]];
                    int neigh_window_cap = windows_manager.capacity[neigh_id[0]][neigh_id[1]];

                    for (int j = 0; j < neigh_window_cap; j ++) {
                        auto other_id = neigh_window[j];
                        calc_excluded_vol_force(ring_id, other_id[0], p_id, other_id[1], true);
                    }
                }
            }
        }

        for (int ring_id = 0; ring_id < num_rings; ring_id++)
        {
            // Springs
            for (int p_id = 0; p_id < num_particles; p_id ++) {
                int id_left = (p_id == 0) ? num_particles-1 : p_id-1;
                int id_right = (p_id == num_particles-1) ? 0 : p_id+1;

                calc_spring_force(ring_id, p_id, id_left);
                calc_spring_force(ring_id, p_id, id_right);
            }

            // Bend
            switch (dynamic_cfg.area_potencial)
            {
            case AreaPotencialType::format:
                format_forces(ring_id);
                break;
            case AreaPotencialType::target_perimeter:
                target_perimeter_forces(ring_id);
                break;
            case AreaPotencialType::target_area:
                target_area_forces(ring_id);
                break;
            }
        }
    }

   void update_windows() {
        #if DEBUG == 1
        rng_manager.update();
        #endif

        windows_manager.update_window_members();

        calc_forces_windows();

        switch (integration_type)
        {
        case 0:
            for (int ring_id = 0; ring_id < num_rings; ring_id++) {
                advance_time(ring_id);
            }
            break;
        case 1:
            advance_time_verlet();
            break;
        }

        #if DEBUG == 1
        update_graph_points();   
        #endif

        sim_time += dt;
        num_time_steps += 1;
   }

    void calc_border_point(int ring_id, array<double, 2> &p1, array<double, 2> &p2, int mid_point_id, bool place_above_p2=false) {
        /**
         * Calcula a posição do ponto médio entre 'p1' e 'p2' utilizado para renderização correta do anel. 
         * Tal ponto é necessário quando a menor reta que conecta 'p1' a 'p2' passa pelas bordas periódicas.
         * 
         * Se 'p1' e 'p2' não estiverem no caso especial, o ponto médio é colocado sobre 'p1' ou 'p2',
         * dependendo do valor de 'place_above_p2'.
         * 
         * Parameters
         * ----------
         * p1, p2:
         *      Pontos do anel.
         * 
         * mid_point_id:
         *      id do ponto médio a ser calculado na variável 'graph_points'. É necessário especificar esse
         *      id pois existem dois pontos médios entre 'p1' e 'p1'.
         * 
         * place_above_p2:
         *      Se é para colocar o ponto médio sobre 'p2'.
         */
        double dx = p2[0] - p1[0];
        double dy = p2[1] - p1[1];
        
        bool calc_intersect = false;
        if (abs(dx) > size * 0.5) {
            calc_intersect = true;
            dx -= copysign(size, dx);
        }
        if (abs(dy) > size * 0.5) {
            calc_intersect = true;
            dy -= copysign(size, dy);
        }

        if (calc_intersect == true) {
            array<array<double, 2>, 2> intersect_p;
            array<double, 2> virtual_p2 = {p1[0] + dx, p1[1] + dy};
            intersect.calc_points(p1, virtual_p2, intersect_p);

            // O vetor dr = (dx, dy) aponta para o ponto de intersecção correto,
            // então, se pi for o ponto de intersecção correto, temos que
            //
            //  k * dr = pi - p1, k > 0
            //
            // Dessa forma, o valor de k pode ser utilizado para achar qual é o
            // ponto de intersecção correto.
            int correct_id; 
            if (dy != 0) {
                correct_id = (intersect_p[0][1] - p1[1])/dy > 0 ? 0 : 1;
            } else {
                correct_id = (intersect_p[0][0] - p1[0])/dx > 0 ? 0 : 1;
            }

            graph_points[ring_id][mid_point_id][0] = intersect_p[correct_id][0];
            graph_points[ring_id][mid_point_id][1] = intersect_p[correct_id][1];
        } else {
            if (place_above_p2) {
                graph_points[ring_id][mid_point_id][0] = p2[0];
                graph_points[ring_id][mid_point_id][1] = p2[1];
            } else {
                graph_points[ring_id][mid_point_id][0] = p1[0];
                graph_points[ring_id][mid_point_id][1] = p1[1];
            }
        }
    }

    void update_graph_points() {
        for (int ring_id = 0; ring_id < num_rings; ring_id++) {
            graph_points[ring_id][0][0] = pos[ring_id][0][0];
            graph_points[ring_id][0][1] = pos[ring_id][0][1];
            
            calc_border_point(ring_id, pos[ring_id][0], pos[ring_id][num_particles-1], 3*num_particles - 1, true);
            calc_border_point(ring_id, pos[ring_id][0], pos[ring_id][1], 1, false);
            for (int p_id = 1; p_id < num_particles; p_id++) {
                int p_graph_id = 3 * p_id;
                
                graph_points[ring_id][p_graph_id][0] = pos[ring_id][p_id][0];
                graph_points[ring_id][p_graph_id][1] = pos[ring_id][p_id][1];
                
                int p2_id = p_id + 1;
                if (p_id == (num_particles-1))
                    p2_id = 0;
                
                array<double, 2> & p_before = pos[ring_id][p_id-1];
                array<double, 2> & p = pos[ring_id][p_id];
                array<double, 2> & p_after = pos[ring_id][p2_id];
                
                calc_border_point(ring_id, p, p_before, p_graph_id - 1, true);
                calc_border_point(ring_id, p, p_after, p_graph_id + 1);
            }
        }
    }

    double mean_vel(int ring_id) {
        double sum_vel[2] = {0, 0};
        for (array<double, 2> vel_i: vel[ring_id]) {
            double speed = sqrt(vel_i[0]*vel_i[0] + vel_i[1]*vel_i[1]);
            
            if (speed == 0)
                continue;

            sum_vel[0] += vel_i[0]/speed;
            sum_vel[1] += vel_i[1]/speed;
        }
        double speed_total = sqrt(sum_vel[0]*sum_vel[0] + sum_vel[1]*sum_vel[1]);
        return speed_total / num_particles;
    }

    array<double, 2> mean_vel_vec(int ring_id) {
        array<double, 2> sum_vel = {0., 0.};
        for (array<double, 2> vel_i: vel[ring_id]) {
            double speed = sqrt(vel_i[0]*vel_i[0] + vel_i[1]*vel_i[1]);
            if (speed == 0)
                continue;

            sum_vel[0] += vel_i[0]/speed;
            sum_vel[1] += vel_i[1]/speed;
        }
        sum_vel[0] /= (double)num_particles;
        sum_vel[1] /= (double)num_particles;
        return sum_vel;
    }
};


// void advance_time_old(int ring_id) {
//         for (int i=0; i < num_particles; i++) {
//             pos[ring_id][i][0] += dt * vel[ring_id][i][0];
//             pos[ring_id][i][1] += dt * vel[ring_id][i][1];

//             #if DEBUG == 1
//             if (vel[ring_id][i][0] > 1e6) {
//                 std::cout << "Error: High velocity" << std::endl;
//             }
            
//             if (isnan(pos[ring_id][i][0]) == true) {
//                 std::cout << "Error: pos nan 1" << std::endl;
//             }
//             #endif

//             #if DEBUG == 1    
//                 auto& rng_nums = rng_manager.get_random_num(i, ring_id);
//                 double rng_rot = (double)rng_nums[0]/(double)RAND_MAX * 2. - 1.;
//                 double rng_trans_x = (double)rng_nums[1]/(double)RAND_MAX * 2. - 1.;
//                 double rng_trans_y = (double)rng_nums[2]/(double)RAND_MAX * 2. - 1.;
//             #else
//                 double rng_rot = (double)rand()/(double)RAND_MAX * 2. - 1.;
//                 double rng_trans_x = (double)rand()/(double)RAND_MAX * 2. - 1.;
//                 double rng_trans_y = (double)rand()/(double)RAND_MAX * 2. - 1.;
//             #endif

//             double noise_rot = rng_rot * sqrt(2. * rot_diff) / sqrt(dt); 
//             double noise_trans_x = rng_trans_x * sqrt(2. * trans_diff) / sqrt(dt); 
//             double noise_trans_y = rng_trans_y * sqrt(2. * trans_diff) / sqrt(dt); 

//             double speed = sqrt(vel[ring_id][i][0]*vel[ring_id][i][0] + vel[ring_id][i][1]*vel[ring_id][i][1]);
            
//             double angle_derivate;
//             if (speed == 0.) {
//                 update_debug.count_zero_speed += 1;
//                 angle_derivate = 0.;
//             } else {
//                 double cross_prod = self_prop_vel[ring_id][i][0] * vel[ring_id][i][1]/speed - self_prop_vel[ring_id][i][1] * vel[ring_id][i][0]/speed;
                
//                 if (abs(cross_prod) > 1) {
//                     #if DEBUG == 1
//                     std::cout << "Error: cross_prod | " << cross_prod << std::endl;
//                     #endif
//                     cross_prod = copysign(1, cross_prod);
//                 }

//                 angle_derivate = 1. / relax_time * asin(cross_prod) + noise_rot;
//             }
            
//             self_prop_angle[ring_id][i] += angle_derivate * dt;

//             vel[ring_id][i][0] = vo * self_prop_vel[ring_id][i][0] + mobility * sum_forces_matrix[ring_id][i][0] + noise_trans_x;
//             vel[ring_id][i][1] = vo * self_prop_vel[ring_id][i][1] + mobility * sum_forces_matrix[ring_id][i][1] + noise_trans_y;

//             self_prop_vel[ring_id][i][0] = cos(self_prop_angle[ring_id][i]);
//             self_prop_vel[ring_id][i][1] = sin(self_prop_angle[ring_id][i]);

//             // for (int i = 0; i < num_particles; i++)
//             // {
//             //     pos[i][0] = remainder(pos[i][0] + size/2., size) + size/2.; 
//             //     pos[i][1] = remainder(pos[i][1] + size/2., size) + size/2.; 
//             // }
            
//             for (int dim = 0; dim < 2.f; dim ++) {
//                 if (pos[ring_id][i][dim] > size/2.f)
//                     pos[ring_id][i][dim] -= size;
//                 else if (pos[ring_id][i][dim] < -size/2.f)
//                     pos[ring_id][i][dim] += size;
//             }

//             #if DEBUG == 1
//             if (isnan(pos[ring_id][i][0]) == true)
//                 std::cout << "Error: pos_nan 2" << std::endl;

//             total_forces[ring_id][i][0] = sum_forces_matrix[ring_id][i][0];
//             total_forces[ring_id][i][1] = sum_forces_matrix[ring_id][i][1];
//             #endif

//             sum_forces_matrix[ring_id][i][0] = 0.f;
//             sum_forces_matrix[ring_id][i][1] = 0.f;
//         }        
//     }