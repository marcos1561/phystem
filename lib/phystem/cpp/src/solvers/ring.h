#include <cmath>
#include <vector>
#include <array>
#include <iostream>
#include <cstdlib> 

#include "../configs/ring.h"
#include "../rng_manager.h"
#include "../macros_defs.h"

#include "../intersections.h"

using Vec2d = std::array<double, 2>;
using PosArray = std::vector<std::array<double, 2>>;

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

struct SpringDebug {
    int count_overlap;
};

struct ExcludedVolDebug {
    int count_overlap;
};

struct AreaDebug {
    int count_overlap;
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

    vector<array<double, 2>> pos; // Posições das partículas
    vector<array<double, 2>> vel; // Velocidades das partículas
    vector<double> self_prop_angle; // Ângulo da direção da velocidade auto propulsora

    RingCfg dynamic_cfg; // Configurações da dinâmica entre as partículas
    double size; // tamanho de uma dimensão do espaço
    double dt; 
    double sim_time;

    int n; // Número de partículas no anel
    
    vector<array<double, 2>> self_prop_vel; // Vetor unitário da velocidade propulsora
    vector<array<double, 2>> sum_forces_matrix; // Matrix com a soma das forças sobre cada partícula


    //==
    // Area Potencial
    //==
    vector<array<double, 2>> differences; // Vetor cujo i-ésimo elemento contém pos[i+1] - pos[i]
    vector<array<double, 2>> pos_continuos; // Posições das partículas de forma contínua;
    //=========//


    //==
    // DEBUG
    //==
    vector<array<double, 2>> total_forces;
    vector<array<double, 2>> spring_forces;
    vector<array<double, 2>> bend_forces;
    vector<array<double, 2>> vol_forces;
    vector<array<double, 2>> area_forces;

    vector<vector<double*>> pos_t = vector<vector<double*>>(2); // Transposta da posições das partículas
    

    // Pontos utilizados na renderização do anel, sua estrutura é a seguinte
    //
    // [p1, pm1_1, pm1_2, p2, pm2_1, pm2_2, p3, pm3_1, pm3_2, p4, ...]
    //
    // Em que p{i} é o i-ésimo ponto no anel e pm{i}_{1, 2} são os pontos médios entre
    // o i-ésimo e (i+1)-ésimo ponto do anel.
    vector<array<double, 2>> graph_points;

    RngManager rng_manager;
    IntersectionCalculator intersect;

    UpdateDebug update_debug = {0};
    SpringDebug spring_debug = {0};
    ExcludedVolDebug excluded_vol_debug = {0};
    AreaDebug area_debug = {0};
    //=========//

    Ring(vector<array<double, 2>> &pos0, vector<array<double, 2>> &vel0, vector<double> self_prop_angle0,
        RingCfg dynamic_cfg, double size, double dt, int seed=-1) 
    : pos(pos0), vel(vel0), self_prop_angle(self_prop_angle0), dynamic_cfg(dynamic_cfg), size(size), dt(dt)
    {
        if (seed != -1.)
            srand(seed);
        else
            srand(time(0));

        n = pos0.size();
        sim_time = 0.0;

        initialize_dynamic();
        
        #if DEBUG == 1
        rng_manager = RngManager(n, 3);
        intersect = IntersectionCalculator(size);
        #endif
    }

    void initialize_dynamic() {
        spring_k = dynamic_cfg.spring_k;
        spring_r = dynamic_cfg.spring_r;
        
        k_bend = dynamic_cfg.k_bend;
        p0 = dynamic_cfg.p0;

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

        for (double angle : self_prop_angle) {
            double vx = cos(angle);
            double vy = sin(angle);
            self_prop_vel.push_back({vx, vy});
        }

        sum_forces_matrix = vector<array<double, 2>>(n, {0., 0.});
        
        differences = vector<array<double, 2>>(n, {0., 0.});
        pos_continuos = vector<array<double, 2>>(n, {0., 0.});

        #if DEBUG == 1
        spring_forces = vector<array<double, 2>>(n, {0., 0.});
        bend_forces = vector<array<double, 2>>(n, {0., 0.});
        vol_forces = vector<array<double, 2>>(n, {0., 0.});
        area_forces = vector<array<double, 2>>(n, {0., 0.});
        total_forces = vector<array<double, 2>>(n, {0., 0.});

        for (int i=0; i < n; i ++) {
            pos_t[0].push_back(&pos[i][0]);
            pos_t[1].push_back(&pos[i][1]);
        }

        graph_points = vector<array<double, 2>>(3*n, {0., 0.});
        
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
 
    void calc_forces_normal() {
        // Excluded volume
        for (int p_id = 0; p_id < n; p_id ++) {
            auto &p = pos[p_id];
            for (int other_id = 0; other_id < n; other_id ++) {
                if (other_id == p_id) {
                    continue;
                }
                auto &other = pos[other_id];

                double dx = p[0] - other[0];
                double dy = p[1] - other[1];

                double dist = periodic_dist(dx, dy);

                if (dist > force_r_lim) { 
                    continue; 
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

                sum_forces_matrix[p_id][0] += vol_fx;
                sum_forces_matrix[p_id][1] += vol_fy;

                #if DEBUG == 1
                vol_forces[p_id][0] += vol_fx;
                vol_forces[p_id][1] += vol_fy;
                #endif
            }
        }

        // Bond
        for (int p_id = 0; p_id < n; p_id ++) {
            int id_left = (p_id == 0) ? n-1 : p_id-1;
            int id_right = (p_id == n-1) ? 0 : p_id+1;

            calc_spring_force(p_id, id_left);
            calc_spring_force(p_id, id_right);
        }

        // Bend
        calc_bend_forces();
    }

    void calc_spring_force(int p_id, int other_id) {
        auto& p = pos[p_id]; 
        auto& other = pos[other_id]; 

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

        sum_forces_matrix[p_id][0] += spring_fx;
        sum_forces_matrix[p_id][1] += spring_fy;

        #if DEBUG == 1
        spring_forces[p_id][0] += spring_fx;
        spring_forces[p_id][1] += spring_fy;
        #endif
    }


    double calc_differences() {
        double perimeter = 0;

        auto n = pos.size();
        double dx, dy;
        for (size_t i = 0; i < (n-1); i++)
        {
            dx = pos[i+1][0] - pos[i][0];
            dy = pos[i+1][1] - pos[i][1];
            perimeter += periodic_dist(dx, dy);
            
            differences[i] = {dx, dy};
        }

        dx = pos[0][0] - pos[n-1][0];
        dy = pos[0][1] - pos[n-1][1];
        perimeter += periodic_dist(dx, dy);

        differences[n-1] = {dx, dy}; 

        return perimeter;
    }

    double calc_area(PosArray& points) {
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

    double calc_perimeter(PosArray& points) {
        double perimeter = 0.0;

        for (size_t i = 0; i < points.size()-1; i++)
        {
            perimeter += vector_dist(points[i], points[i+1]);
        }
        int i = points.size() - 1;
        perimeter += vector_dist(points[i], points[0]);

        return perimeter;
    }

    void calc_bend_force(int point_id, double area, double perimeter) {
        int id = pos_continuos.size() - 1;
        if (point_id != 0)
            id = point_id - 1;
        auto& v1 = pos_continuos[id];
        
        id = 0;
        if (point_id != (pos_continuos.size() - 1))
            id = point_id + 1;
        auto& v2 = pos_continuos[id];

        auto& point = pos_continuos[point_id]; 

        double d1 = vector_dist(v1, pos_continuos[point_id]);
        double d2 = vector_dist(v2, pos_continuos[point_id]);

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
        area_forces[point_id][0] = -gradient_x;
        area_forces[point_id][1] = -gradient_y;
        #endif

        sum_forces_matrix[point_id][0] -= gradient_x;
        sum_forces_matrix[point_id][1] -= gradient_y;
    }

    void calc_bend_forces() {
        double perimeter = calc_differences();

        pos_continuos[0] = pos[0];
        for (size_t i = 0; i < (differences.size()-1); i++)
        {
            pos_continuos[i+1][0] = pos_continuos[i][0] + differences[i][0];
            pos_continuos[i+1][1] = pos_continuos[i][1] + differences[i][1];
        }

        double area = calc_area(pos_continuos);
        
        for (size_t i = 0; i < pos_continuos.size(); i++)
        {
            calc_bend_force(i, area, perimeter);
        }
    }

    void advance_time() {
        for (int i=0; i < n; i++) {
            pos[i][0] += dt * vel[i][0];
            pos[i][1] += dt * vel[i][1];

            if (vel[i][0] > 1e6) {
                std::cout << "merda" << std::endl;
            }
            
            if (isnan(pos[i][0]) == true) {
                std::cout << "merda" << std::endl;
            }

            #if DEBUG == 1    
                auto& rng_nums = rng_manager.get_random_num(i);
                double rng_rot = (double)rng_nums[0]/(double)RAND_MAX * 2. - 1.;
                double rng_trans_x = (double)rng_nums[1]/(double)RAND_MAX * 2. - 1.;
                double rng_trans_y = (double)rng_nums[2]/(double)RAND_MAX * 2. - 1.;
            #else
                double rng_rot = (double)rand()/(double)RAND_MAX * 2. - 1.;
                double rng_trans = (double)rand()/(double)RAND_MAX * 2. - 1.;
            #endif

            double noise_rot = rng_rot * sqrt(2. * rot_diff) / sqrt(dt); 
            double noise_trans_x = rng_trans_x * sqrt(2. * trans_diff) / sqrt(dt); 
            double noise_trans_y = rng_trans_y * sqrt(2. * trans_diff) / sqrt(dt); 

            double speed = sqrt(vel[i][0]*vel[i][0] + vel[i][1]*vel[i][1]);
            
            double angle_derivate;
            if (speed == 0.) {
                update_debug.count_zero_speed += 1;
                angle_derivate = 0.;
            } else {
                double cross_prod = self_prop_vel[i][0] * vel[i][1]/speed - self_prop_vel[i][1] * vel[i][0]/speed;
                
                if ((cross_prod > 1) | (cross_prod < -1)) {
                    std::cout << "merda" << std::endl;
                }

                angle_derivate = 1. / relax_time * asin(cross_prod) + noise_rot;
            }
            
            self_prop_angle[i] += angle_derivate * dt;

            vel[i][0] = vo * self_prop_vel[i][0] + mobility * sum_forces_matrix[i][0] + noise_trans_x;
            vel[i][1] = vo * self_prop_vel[i][1] + mobility * sum_forces_matrix[i][1] + noise_trans_y;

            self_prop_vel[i][0] = cos(self_prop_angle[i]);
            self_prop_vel[i][1] = sin(self_prop_angle[i]);

            // for (int i = 0; i < n; i++)
            // {
            //     pos[i][0] = remainder(pos[i][0] + size/2., size) + size/2.; 
            //     pos[i][1] = remainder(pos[i][1] + size/2., size) + size/2.; 
            // }
            
            for (int dim = 0; dim < 2.f; dim ++) {
                if (pos[i][dim] > size/2.f)
                    pos[i][dim] -= size;
                else if (pos[i][dim] < -size/2.f)
                    pos[i][dim] += size;
            }

            if (isnan(pos[i][0]) == true) {
                std::cout << "merda" << std::endl;
            }

            #if DEBUG == 1
            total_forces[i][0] = sum_forces_matrix[i][0];
            total_forces[i][1] = sum_forces_matrix[i][1];
            #endif

            sum_forces_matrix[i][0] = 0.f;
            sum_forces_matrix[i][1] = 0.f;
        }
    }

    void update_normal() {
        #if DEBUG == 1
        rng_manager.update();
        
        for (int i = 0; i < n; i++)
        {
           spring_forces[i][0] = 0.;
           spring_forces[i][1] = 0.;
           
           vol_forces[i][0] = 0.;
           vol_forces[i][1] = 0.;
        }
        #endif

        calc_forces_normal();
        advance_time();

        #if DEBUG == 1
        update_graph_points();   
        #endif

        sim_time += dt;
    }
   

    void calc_border_point(array<double, 2> &p1, array<double, 2> &p2, int mid_point_id, bool place_above_p2=false) {
        /**
         * Calcula a posição do ponto médio entre 'p1' e 'p2' utilizado para renderização correta do anel. 
         * Tal ponto é necessário quando a menor reta que linha 'p1' a 'p2' passa pelas bordas periódicas.
         * 
         * Se 'p1' e 'p2' não estiverem no caso especial, o ponto médio é colocado sobre 'p1' ou 'p2',
         * dependendo do valor de 'place_above-p2'.
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

            graph_points[mid_point_id][0] = intersect_p[correct_id][0];
            graph_points[mid_point_id][1] = intersect_p[correct_id][1];
        } else {
            if (place_above_p2) {
                graph_points[mid_point_id][0] = p2[0];
                graph_points[mid_point_id][1] = p2[1];
            } else {
                graph_points[mid_point_id][0] = p1[0];
                graph_points[mid_point_id][1] = p1[1];
            }
        }
    }

    void update_graph_points() {
        graph_points[0][0] = pos[0][0];
        graph_points[0][1] = pos[0][1];
        
        calc_border_point(pos[0], pos[n-1], 3*n - 1, true);
        calc_border_point(pos[0], pos[1], 1, false);
        for (int p_id = 1; p_id < n; p_id++) {
            int p_graph_id = 3 * p_id;
            
            graph_points[p_graph_id][0] = pos[p_id][0];
            graph_points[p_graph_id][1] = pos[p_id][1];
            
            int p2_id = p_id + 1;
            if (p_id == (n-1))
                p2_id = 0;
            
            array<double, 2> & p_before = pos[p_id-1];
            array<double, 2> & p = pos[p_id];
            array<double, 2> & p_after = pos[p2_id];
            
            calc_border_point(p, p_before, p_graph_id - 1, true);
            calc_border_point(p, p_after, p_graph_id + 1);
        }
    }


    double mean_vel() {
        double sum_vel[2] = {0, 0};
        for (array<double, 2> vel_i: vel) {
            double speed = sqrt(vel_i[0]*vel_i[0] + vel_i[1]*vel_i[1]);
            
            if (speed == 0)
                continue;

            sum_vel[0] += vel_i[0]/speed;
            sum_vel[1] += vel_i[1]/speed;
        }
        double speed_total = sqrt(sum_vel[0]*sum_vel[0] + sum_vel[1]*sum_vel[1]);
        return speed_total / n;
    }

    array<double, 2> mean_vel_vec() {
        array<double, 2> sum_vel = {0., 0.};
        for (array<double, 2> vel_i: vel) {
            double speed = sqrt(vel_i[0]*vel_i[0] + vel_i[1]*vel_i[1]);
            if (speed == 0)
                continue;

            sum_vel[0] += vel_i[0]/speed;
            sum_vel[1] += vel_i[1]/speed;
        }
        sum_vel[0] /= (double)n;
        sum_vel[1] /= (double)n;
        return sum_vel;
    }
};