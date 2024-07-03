#include <cmath>
#include <vector>
#include <random>
#include <array>
#include <map>
#include <iostream>
#include <cstdlib> 
#include <omp.h>
#include <forward_list>
#include <algorithm>

#include "../configs/ring.h"
#include "../rng_manager.h"
#include "../windows_manager.h"
#include "../in_pol_checker.h"
#include "../macros_defs.h"

#include "../intersections.h"

using Vec2d = std::array<double, 2>;
using Vector2d = std::vector<std::array<double, 2>>;
using Vector3d = std::vector<std::vector<std::array<double, 2>>>;

using ColInfo = InPolChecker::ColInfo;

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

template <typename T>
void remove_by_indices(std::forward_list<T>& flist, std::vector<size_t>& indices) {
    /* Remove os items em `flist` de índices `indices`. */
    // Sort indices in descending order
    std::sort(indices.begin(), indices.end());

    for (auto idx : indices) {
        if (idx >= flist.max_size()) {
            throw std::out_of_range("Index out of range");
        }
    }

    auto prev = flist.before_begin();
    for (auto idx = indices.rbegin(); idx != indices.rend(); ++idx) {
        prev = flist.before_begin();
        for (size_t i = 0; i < *idx; ++i) {
            ++prev;
        }
        flist.erase_after(prev);
    }
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
    bool high_vel;
};

class UniqueId {
public:
    unsigned long int max_id;
    
    UniqueId() : max_id(0) {}

    unsigned long int new_id() {
        max_id += 1;
        return max_id;
    }
};

class ResolvedInv {
public:
    struct Invasion {
        ColInfo col;
        int num_steps_elapsed;
    };

    std::forward_list<Invasion> invasions;

    void add_collision(ColInfo col_info) {
        invasions.push_front(Invasion{col_info, 0});
    }

    void remove_ids(vector<size_t> indices) {
        remove_by_indices(invasions, indices);
    }

    // vector<bool> resolved;
    // int num_active;
    // vector<int> active_ids;

    // void add_collision(ColInfo col_info) {
    //     bool has_added = false;
    //     int added_id;
    //     for (size_t i = 0; i < resolved.size(); i++)
    //     {
    //         if (resolved[i]) {
    //             added_id = i;
    //             collisions[i] = col_info;
    //             resolved[i] = false;
    //             has_added = true;
    //         }
    //     }

    //     if (!has_added) {
    //         added_id = resolved.size();
    //         collisions.push_back(col_info);
    //         resolved.push_back(false);
    //     }
    // }
};

class Ring {
public:
    // Dynamic Configs
    double spring_k;
    double spring_r;

    double k_area;
    double k_format;
    double p0;
    double p0_format;
    double area0;
    double p_target;
    
    double k_invasion;

    double mobility;
    double relax_time;
    double vo;

    double trans_diff;
    double rot_diff;

    double diameter; 
    double max_dist;
    double adh_force;
    double rep_force;

    // State info
    Vector3d pos; // Posições das partículas
    Vector3d vel; // Velocidade das partículas
    vector<double> self_prop_angle; // Ângulo da direção da velocidade auto propulsora
    int num_particles; // Número de partículas em cada anel
    
    // Rings ids
    int num_active_rings; 
    vector<bool> mask;
    vector<int> rings_ids; // ids dos anéis ativos no array de anéis 
    vector<unsigned long int> unique_rings_ids; // uids dos anéis ativos
    UniqueId unique_id_mng;

    Vector3d old_pos; 
    vector<vector<double>> old_self_prop_angle;

    RingCfg dynamic_cfg; // Configurações da dinâmica entre as partículas
    double height; // tamanho de uma dimensão do espaço
    double length; // tamanho de uma dimensão do espaço
    double dt; 
    const RingUpdateType update_type;
    const RingIntegrationType integration_type;

    // dt variável (não utilizado no momento)
    double base_dt;
    double low_dt;
    int num_low_dt;
    int dt_count;
    bool is_low_dt;


    double sim_time;
    int num_time_steps;

    int num_max_rings; 
    double ring_radius;

    Vector3d* continuos_ring_positions;

    Vector3d sum_forces_matrix; // Matrix com a soma das forças sobre cada partícula
    Vector2d center_mass;

    WindowsManagerRing windows_manager;
    InPolChecker in_pol_checker;
    ResolvedInv resolved_invs;
    int steps_after_resolved;
    
    bool to_recalculate_ids = false;

    // Stokes
    StokesCfg stokes_cfg;
    double max_create_border;

    vector<vector<array<int, 2>>> create_rings_win_ids;
    vector<bool> to_create_new_ring;
    vector<array<int, 2>> begin_windows_ids;
    vector<Vector2d> stokes_init_pos;
    double stokes_init_self_angle;
    int num_created_rings;

    double create_border;
    double remove_border;

    // Invagination
    std::map<int, double> inv_spring_k;
    std::map<int, bool> inv_is_rfix;
    std::map<int, bool> inv_is_lfix;
    int inv_num_affected;

    // Area Potencial
    Vector3d differences; // Vetor cujo i-ésimo elemento contém pos[i+1] - pos[i]
    Vector3d pos_continuos; // Posições das partículas de forma contínua

    // RK4
    // (k_i, anel, partícula, [x, y, theta])
    vector<vector<vector<array<double, 3>>>> k_matrix;

    //==
    // DEBUG
    //==
    Vector3d total_forces;
    Vector3d spring_forces;
    Vector3d vol_forces;
    Vector3d area_forces;
    Vector3d obs_forces;
    Vector3d format_forces;
    Vector3d invasion_forces;

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

    UpdateDebug update_debug = {0, false};
    SpringDebug spring_debug = {0};
    ExcludedVolDebug excluded_vol_debug = {0};
    AreaDebug area_debug = {0};
    //=========//

    Ring(Vector3d &pos0, vector<double>& self_prop_angle0, int num_particles, RingCfg dynamic_cfg, 
        double height, double length, double dt, ParticleWindowsCfg particle_windows_cfg,
        RingUpdateType update_type=RingUpdateType::periodic_borders, RingIntegrationType integration_type=RingIntegrationType::euler, 
        StokesCfg stokes_cfg=StokesCfg(), InPolCheckerCfg in_pol_checker_cfg=InPolCheckerCfg(3, 3, 1, 1, true), int seed=-1) 
    : num_particles(num_particles), dynamic_cfg(dynamic_cfg), height(height), length(length), dt(dt),
    update_type(update_type), integration_type(integration_type), 
    stokes_cfg(stokes_cfg) 
    {
        int NTHREADS = omp_get_max_threads();
        std::cout << "Número de Threads disponíveis: " << NTHREADS << std::endl;

        // if ((update_type == RingUpdateType::stokes) && 
        //     (dynamic_cfg.area_potencial != AreaPotencialType::target_area)) 
        // {
        //     throw std::invalid_argument("O modo 'stokes' apenas suporta 'area_potencial' = 'target_area'.");
        // }

        if (seed != -1.)
            srand(seed);
        else
            srand(time(0));

        // Inicialização dos anéis na memória
        if (stokes_cfg.num_max_rings > 0) {
            num_max_rings = stokes_cfg.num_max_rings;
        } else {
            num_max_rings = pos0.size(); 
        }

        num_active_rings = pos0.size();
        
        auto zero_vector_1d = vector<double>(num_particles, 0.); 
        auto zero_vector_2d = vector<array<double, 2>>(num_particles, {0., 0.}); 

        pos = Vector3d(num_max_rings, zero_vector_2d);
        vel = Vector3d(num_max_rings, zero_vector_2d);
        self_prop_angle =  vector<double>(num_max_rings);
        mask = vector<bool>(num_max_rings);
        rings_ids = vector<int>(num_max_rings);
        unique_rings_ids = vector<unsigned long int>(num_max_rings);

        unique_id_mng = UniqueId();

        for (int i = 0; i < num_max_rings; i++)
        {   
            if (i < num_active_rings) {
                pos[i] = pos0[i];
                self_prop_angle[i] = self_prop_angle0[i];

                mask[i] = true;
                rings_ids[i] = i;
                unique_rings_ids[i] = unique_id_mng.new_id();
            } else {
                mask[i] = false;
            }
        }
        
        num_max_rings = pos.size();
        ring_radius = dynamic_cfg.diameter / sqrt(2. * (1. - cos(2.*M_PI/((double)num_particles))));
        
        continuos_ring_positions = &pos_continuos;
        if (update_type == RingUpdateType::stokes)
            continuos_ring_positions = &pos;

        std::cout << "ring_radius: " << ring_radius << std::endl;

        sim_time = 0.0;
        num_time_steps = 0;
        
        // Variable dt
        base_dt = dt;
        low_dt = 0.001;
        num_low_dt = (int)(base_dt/low_dt) * 100;
        dt_count = 0;
        is_low_dt = false;

        initialize_dynamic();
        
        SpaceInfo space_info(height, length);
        windows_manager = WindowsManagerRing(&pos, &rings_ids, &num_active_rings, particle_windows_cfg.num_cols, 
            particle_windows_cfg.num_rows, space_info, particle_windows_cfg.update_freq);
        
        in_pol_checker = InPolChecker(continuos_ring_positions, &center_mass, &rings_ids, &num_active_rings, 
            height, length, in_pol_checker_cfg.num_cols_windows, in_pol_checker_cfg.num_rows_windows, 
            in_pol_checker_cfg.update_freq, in_pol_checker_cfg.disable);
        steps_after_resolved = in_pol_checker_cfg.steps_after;

        if (update_type == RingUpdateType::stokes) {
            init_stokes();
        }
        
        #if DEBUG == 1
        rng_manager = RngManager(num_particles, num_max_rings, 5);
        intersect = IntersectionCalculator(height, length);
        #endif
    }

    void initialize_dynamic() {
        spring_k = dynamic_cfg.spring_k;
        spring_r = dynamic_cfg.spring_r;
        
        k_area = dynamic_cfg.k_area;
        k_format = dynamic_cfg.k_format;
        p0 = dynamic_cfg.p0;
        p0_format = dynamic_cfg.p0_format;
        area0 = dynamic_cfg.area0;
        p_target = p0 * sqrt(area0);

        k_invasion = dynamic_cfg.k_invasion;

        mobility = dynamic_cfg.mobility;
        relax_time = dynamic_cfg.relax_time;
        vo = dynamic_cfg.vo;

        trans_diff = dynamic_cfg.trans_diff;
        rot_diff = dynamic_cfg.rot_diff;

        diameter = dynamic_cfg.diameter;
        max_dist = dynamic_cfg.max_dist;
        adh_force = dynamic_cfg.adh_force;
        rep_force = dynamic_cfg.rep_force;

        // Lennard-jones stuff
        // diameter_six = pow(diameter, 6.); 
        // diameter_twelve = pow(diameter, 12.); 
        // force_r_lim = pow(2, 1./6.) * diameter;

        auto zero_vector_1d = vector<double>(num_particles, 0.); 
        auto zero_vector_2d = vector<array<double, 2>>(num_particles, {0., 0.}); 

        if ((integration_type == RingIntegrationType::verlet) | 
            (integration_type == RingIntegrationType::rk4)
        ) {
            old_pos = Vector3d(num_max_rings, zero_vector_2d);
            old_self_prop_angle = vector<vector<double>>(num_max_rings, zero_vector_1d);
        }
        
        sum_forces_matrix = Vector3d(num_max_rings, zero_vector_2d);
        
        if (update_type != RingUpdateType::stokes) {
            pos_continuos = Vector3d(num_max_rings, zero_vector_2d);
            differences = Vector3d(num_max_rings, zero_vector_2d);
        } else {
            #if DEBUG == 1
            differences = Vector3d(num_max_rings, zero_vector_2d);
            #endif
        }
        
        center_mass = Vector2d(num_max_rings);

        // rk4 stuff
        if (integration_type == RingIntegrationType::rk4) {
            auto deriv_particles = vector<array<double, 3>>(num_particles, {0., 0., 0.});
            auto deriv_rings = vector<vector<array<double, 3>>>(num_max_rings, deriv_particles);
            k_matrix = vector<vector<vector<array<double, 3>>>>(4, deriv_rings);
        }

        #if DEBUG == 1
        spring_forces = Vector3d(num_max_rings, zero_vector_2d);
        vol_forces = Vector3d(num_max_rings, zero_vector_2d);
        area_forces = Vector3d(num_max_rings, zero_vector_2d);
        total_forces = Vector3d(num_max_rings, zero_vector_2d);
        obs_forces = Vector3d(num_max_rings, zero_vector_2d);
        format_forces = Vector3d(num_max_rings, zero_vector_2d);
        invasion_forces = Vector3d(num_max_rings, zero_vector_2d);

        area_debug.area = vector<double>(num_max_rings);

        pos_t = vector<vector<vector<double*>>>(num_max_rings, vector<vector<double*>>(2));
        for (int i=0; i < num_max_rings; i ++) {
            for (int j = 0; j < num_particles; j++)
            {
                pos_t[i][0].push_back(&pos[i][j][0]);
                pos_t[i][1].push_back(&pos[i][j][1]);
            }
        }

        graph_points = Vector3d(num_max_rings, vector<array<double, 2>>(3*num_particles, {0., 0.}));
        
        update_graph_points();
        #endif
    }

    void init_stokes() {
        /** Inicializa os dados relacionados ao fluxo de stokes */
        
        // Limite no eixo x da região de criação/remoção de novos anéis.
        create_border = -length/2 + stokes_cfg.create_length;
        remove_border = length/2 - stokes_cfg.remove_length;

        /**
         * Cálculo das janelas (a nível das partículas) que estão dentro
         * da região de criação de anéis. O id de tais janelas são armazenados 
         * em 'begin_windows_ids'.
        */
        max_create_border = create_border;
        for (auto window_id: windows_manager.windows_ids) {
            auto center_pos = windows_manager.windows_center[window_id[0]][window_id[1]];
            
            double left_window_border = center_pos[0] - windows_manager.window_length/2.;
            if (left_window_border < create_border) {
                double right_window_border = center_pos[0] + windows_manager.window_length/2.;
                
                // Garantindo que 'max_create_border' seja realmente o máximo. 
                if (right_window_border > max_create_border) {
                    max_create_border = right_window_border;
                }

                begin_windows_ids.push_back(window_id);
            }
        }
        std::cout << "Num begin_windows: " << begin_windows_ids.size() << std::endl;


        /**
         * Posição dos anéis que serão criados:
         * 
         * A região de criação é dividida em retângulos e as posições
         * dos anéis são pré-calculadas para eles aparecerem
         * dentro de algum desses retângulos. Quando um retângulo
         * fica livre, um anel é criado nele.
        */
        vector<double> begin_rings_centery;
        
        // Espaçamento vertical entre os anéis
        double y_pad = (diameter * 0.5 * 3.) * 0.5;
        
        // Quantidade de anéis que cabem na região de criação.
        int n = (int)(height / (2.0 * (y_pad + ring_radius)));
        
        std::cout << "Create ring num: " << n << std::endl;

        // Cálculo da posição e do ângulo da velocidade autopropulsora
        // utilizados na criação dos anéis.
        Vector2d stokes_init_pos_i(num_particles);
        double angle = M_PI * 2. / num_particles;
        for (int ring_i = 0; ring_i < n; ring_i++)
        {
            double y_pos = height * 0.5 - (y_pad + ring_radius) * (1.0 + (double)(ring_i * 2));
            begin_rings_centery.push_back(y_pos);
            for (int i = 0; i < num_particles; i++)
            {
                double x = ring_radius * cos((double)i * angle);
                x += -length/2. + 1.1 * ring_radius;

                double y = ring_radius * sin((double)i * angle);
                y += y_pos;
                stokes_init_pos_i[i] = {x, y};
            }

            stokes_init_pos.push_back(stokes_init_pos_i);
        }
        
        
        // int num_angles = 10;
        // std::random_device dev;
        // std::mt19937 rng(dev());
        // std::uniform_int_distribution<std::mt19937::result_type> int_dist(1, num_angles); // distribution in range [1, 6]

        // for (int i = 0; i < num_angles; i++)
        // {
        //     double angle = -M_PI/2. + (double)i/(double)(num_angles-1) * M_PI;
        //     stokes_init_self_angle.push_back(angle);
        // }
        stokes_init_self_angle = 0.0;

        /**
         * Cálculo das janelas que contém a região onde os anéis são criados.
         * 
         * O elemento 'create_rings_win_ids[i]' contém os ids das janelas que estão
         * dentro da região onde o i-ésimo anel é criado.
        */
        float start_y = height/2.;
        float end_y = (begin_rings_centery[1] + begin_rings_centery[0]) * 0.5;
        for (size_t i = 0; i < begin_rings_centery.size(); i++)
        {
            vector<array<int, 2>> ring_win_ids;
            for (auto window_id: begin_windows_ids) {
                auto win_center = windows_manager.windows_center[window_id[0]][window_id[1]];
                double h = windows_manager.window_height;
                if ((win_center[1] - h*0.5 < start_y) && (win_center[1] + h*0.5 > end_y)) {
                    ring_win_ids.push_back(window_id);
                }
            }
            create_rings_win_ids.push_back(ring_win_ids);
            to_create_new_ring.push_back(false);
            start_y = end_y;
            
            if (i < begin_rings_centery.size()-2) {
                end_y = (begin_rings_centery[i+2] + begin_rings_centery[i+1]) * 0.5;
            } else if (i < begin_rings_centery.size()-1) {
                end_y = -height * 0.5;
            }
        }

        calc_center_mass();
        windows_manager.update_window_members();
        in_pol_checker.update();
        recalculate_rings_ids();
    }

    void init_invagination(int height, int length, double upper_k, double bottom_k, int num_affected) {
        inv_num_affected = num_affected;

        for (int i = 0; i < num_particles; i++) {
            inv_spring_k[i] = spring_k;
            inv_is_rfix[i] = false;
            inv_is_lfix[i] = false;
        }

        // Ring of rings
        for (int j = 0; j < length; j++) {
            inv_spring_k[j] = bottom_k;
        }
        
        int id = length+height-2;
        while (id < (num_particles - height + 2)) {
            inv_spring_k[id] = upper_k;
            id ++;
        }
        
        for (int i = 0; i < num_particles; i++)
        {
            std::cout << i << ": " << inv_spring_k[i] << std::endl;
        }
        std::cout << "num_affected: " << inv_num_affected << std::endl;

        // Fix borders
        // for (int j = 0; j < length-1; j++) {
        //     inv_spring_k[2*height + length - 3 + j] = upper_k;
        //     inv_spring_k[height - 1 + j] = bottom_k;
        // }
        
        // for (int j = 0; j < height; j++) {
        //     inv_is_lfix[j] = true;
        //     inv_is_rfix[height+length-2+j] = true;
        // }
    }

    void load_checkpoint(Vector3d& pos_cp, vector<double>& angle_cp, 
        vector<int>& ids_cp, vector<unsigned long int>& uids_cp) {
        /*Método para setar os uids em um carregamento de checkpoint*/
        
        for (size_t i = 0; i < mask.size(); i++) {
            mask[i] = false;
        }

        for (size_t i = 0; i < ids_cp.size(); i++) {
            int id = ids_cp[i];
            
            pos[id] = pos_cp[i];
            self_prop_angle[id] = angle_cp[i];
            unique_rings_ids[id] = uids_cp[i];
            mask[id] = true;
            rings_ids[i] = id;
        }
        auto max_uid = *std::max_element(uids_cp.begin(), uids_cp.end()); 
        unique_id_mng.max_id = max_uid;
    }

    void recalculate_rings_ids() {
        /**
         * Recalcula a lista dos ids dos anéis que estão
         * atualmente ativos. Aqui o id é a posição do anel
         * no vetor global de posições (pos).
        */
        to_recalculate_ids = false;
        int next_id = 0;
        for (int i = 0; i < num_max_rings; i++) {
            if (mask[i] == true) {
                rings_ids[next_id] = i;
                next_id += 1;
            }
        }
        num_active_rings = next_id;
    }

    void add_ring(int add_ring_id) {
        /**
         * Adiciona o anel de id 'add_ring_id' da lista das posições
         * pré-calculadas ('stokes_init_pos').
        */
        for (size_t i = 0; i < mask.size(); i++) {
            if (mask[i] == false) {
                unique_rings_ids[i] = unique_id_mng.new_id();
                pos[i] = stokes_init_pos[add_ring_id];
                
                self_prop_angle[i] = stokes_init_self_angle;
                // double angle = stokes_init_self_angle[int_dist(rng)];
                // std::cout << "angulo: " << angle << std::endl;
                // for (int j = 0; j < num_particles; i++)
                // {
                //     self_prop_angle[i][j] = angle;
                // }

                mask[i] = true;
                num_active_rings += 1;
                to_recalculate_ids = true;
                
                calc_ring_center_mass(i);
                windows_manager.update_entity(i);
                in_pol_checker.windows_manager.update_point(i);
                return;
            }
        }

        std::cout << "Não foi encontrado posições disponíveis para adicionar os anéis." << std::endl;
    }

    void remove_ring(int ring_id) {
        mask[ring_id] = false;
        num_active_rings -= 1;
        to_recalculate_ids = true;
    }

    void periodic_border(array<double, 2>& p){
        /**
         * Dado o vetor 'p' calculado como a diferença entre dois pontos,
         * atualiza o mesmo levando em consideração as bordas periódicas.
        */
        if (abs(p[0]) > length/2.f)
            p[0] -= copysign(length, p[0]);
        
        if (abs(p[1]) > height/2.f)
            p[1] -= copysign(height, p[1]);
    }

    double periodic_dist(double &dx, double &dy) {
        /**
         * Retorna a distância baseado no tipo de atualização.
         * 
         * -> stokes
         *  Distância cartesiana.
         * 
         * -> periodic_boarder | invagination
         *  Distância considerando as bordas periódicas, dado a 
         *  diferença entre dois pontos (sem considerar as bordas periódicas) "dx" e "dy".
         *  
         *  OBS: Esse método atualiza 'dx' e 'dy' para ficarem de acordo com as bordas periódicas.
        */
        if (update_type == RingUpdateType::stokes) {
            return sqrt(dx*dx + dy*dy);
        } 

        if (abs(dx) > length * 0.5)
            dx -= copysign(length, dx);

        if (abs(dy) > height * 0.5)
            dy -= copysign(height, dy);

        return sqrt(dx*dx + dy*dy);
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

        #if DEBUG == 1                
        if (dist == 0.) {
            excluded_vol_debug.count_overlap += 1;
        }
        #endif

        //===
        // Forças lineares atrativas e repulsivas
        //===
        if (dist > max_dist) {
            return;
        }

        double force_r;
        if (dist > diameter) {
            // Força atrativa
            force_r = adh_force * (diameter - dist) / (max_dist - diameter);
        } else {
            // Força repulsiva
            force_r = rep_force * (diameter - dist) / (diameter);
        }
        
        double vol_fx = force_r/dist * dx;
        double vol_fy = force_r/dist * dy;
        //===

        //===
        // Lennard Jones (Sem atração)
        //===
        // if (dist > force_r_lim) { 
        //     return; 
        // } 

        // double force_intensity = exclusion_vol * (0.5 * diameter_six / pow(dist, 7.) - diameter_twelve/pow(dist, 13.) );
        // force_intensity = abs(force_intensity);

        // double vol_fx = force_intensity/dist * dx;
        // double vol_fy = force_intensity/dist * dy;
        //=========

        #pragma omp atomic
        sum_forces_matrix[ring_id][p_id][0] += vol_fx;
        #pragma omp atomic
        sum_forces_matrix[ring_id][p_id][1] += vol_fy;
        
        if (use_third_law) {
            #pragma omp atomic
            sum_forces_matrix[other_ring_id][other_id][0] -= vol_fx;
            #pragma omp atomic
            sum_forces_matrix[other_ring_id][other_id][1] -= vol_fy;
        }

        #if DEBUG == 1
        #pragma omp atomic
        vol_forces[ring_id][p_id][0] += vol_fx;
        #pragma omp atomic
        vol_forces[ring_id][p_id][1] += vol_fy;
        
        if (use_third_law) {
            #pragma omp atomic
            vol_forces[other_ring_id][other_id][0] -= vol_fx;
            #pragma omp atomic
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

    void calc_spring_force2(int ring_id, int spring_id) {
        int first_id = spring_id;
        int second_id = spring_id == (num_particles-1) ? 0 : spring_id + 1;

        auto& p = pos[ring_id][first_id]; 
        auto& other = pos[ring_id][second_id]; 

        double dx = other[0] - p[0];         
        double dy = other[1] - p[1];

        double dist = periodic_dist(dx, dy);

        #if DEBUG == 1                
        if (dist == 0.) {
            spring_debug.count_overlap += 1;
        }
        #endif

        double current_spring_k = spring_k;
        if (update_type == RingUpdateType::invagination) {
            // current_spring_k = inv_spring_k[spring_id];
            if (ring_id < inv_num_affected) {
                current_spring_k = inv_spring_k[spring_id];
            }
        }                

        double force_intensity = current_spring_k * (dist - spring_r);         

        double spring_fx = dx/dist * force_intensity;
        double spring_fy = dy/dist * force_intensity;

        sum_forces_matrix[ring_id][first_id][0] += spring_fx;
        sum_forces_matrix[ring_id][first_id][1] += spring_fy;
        sum_forces_matrix[ring_id][second_id][0] -= spring_fx;
        sum_forces_matrix[ring_id][second_id][1] -= spring_fy;

        #if DEBUG == 1
        spring_forces[ring_id][first_id][0] += spring_fx;
        spring_forces[ring_id][first_id][1] += spring_fy;
        spring_forces[ring_id][second_id][0] -= spring_fx;
        spring_forces[ring_id][second_id][1] -= spring_fy;
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

    void calc_ring_center_mass(int ring_id) {
        auto& ring = (*continuos_ring_positions)[ring_id];

        auto &cm = center_mass[ring_id];
        cm[0] = 0;
        cm[1] = 0;

        for (auto & particle: ring) {
            cm[0] += particle[0];
            cm[1] += particle[1];
        }

        cm[0] /= num_particles;
        cm[1] /= num_particles;

        periodic_border(cm);
    }

    void calc_center_mass() {
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        #pragma omp parallel for schedule(dynamic, 10)
        for (int i = 0; i < num_active_rings; i++) 
        {
            int ring_id = rings_ids[i];
            calc_ring_center_mass(ring_id);
        }
    }

    double calc_continuos_pos(int ring_id) {
        double perimeter = calc_differences(ring_id);

        pos_continuos[ring_id][0] = pos[ring_id][0];
        for (size_t i = 0; i < (differences[ring_id].size()-1); i++)
        {
            pos_continuos[ring_id][i+1][0] = pos_continuos[ring_id][i][0] + differences[ring_id][i][0];
            pos_continuos[ring_id][i+1][1] = pos_continuos[ring_id][i][1] + differences[ring_id][i][1];
        }

        return perimeter;
    }

    void format_force(int ring_id, int point_id, double area, double perimeter) {
        int id = (*continuos_ring_positions)[ring_id].size() - 1;
        if (point_id != 0)
            id = point_id - 1;
        auto& v1 = (*continuos_ring_positions)[ring_id][id];
        
        id = 0;
        if (point_id != ((int)(*continuos_ring_positions)[ring_id].size() - 1))
            id = point_id + 1;
        auto& v2 = (*continuos_ring_positions)[ring_id][id];

        auto& point = (*continuos_ring_positions)[ring_id][point_id]; 

        double d1 = vector_dist(v1, (*continuos_ring_positions)[ring_id][point_id]);
        double d2 = vector_dist(v2, (*continuos_ring_positions)[ring_id][point_id]);

        #if DEBUG == 1                
        if (d1 == 0.)
            area_debug.count_overlap += 1;
        if (d2 == 0.) 
            area_debug.count_overlap += 1;
        #endif

        double delta_area = area - (perimeter/p0_format) * (perimeter/p0_format);

        double area_0_deriv_x = 2.0 * perimeter / (p0_format*p0_format) * ((v1[0] - point[0]) / d1 +  (v2[0] - point[0]) / d2);
        double area_0_deriv_y = 2.0 * perimeter / (p0_format*p0_format) * ((v1[1] - point[1]) / d1 +  (v2[1] - point[1]) / d2);
        
        double gradient_x = k_format * delta_area * ((v2[1] - v1[1])/2.0 + area_0_deriv_x);
        double gradient_y = k_format * delta_area * (-(v2[0] - v1[0])/2.0 + area_0_deriv_y);

        #if DEBUG == 1
        format_forces[ring_id][point_id][0] = -gradient_x;
        format_forces[ring_id][point_id][1] = -gradient_y;
        #endif

        sum_forces_matrix[ring_id][point_id][0] -= gradient_x;
        sum_forces_matrix[ring_id][point_id][1] -= gradient_y;
    }

    void calc_format_forces(int ring_id) {
        double perimeter;
        if (update_type == RingUpdateType::stokes) {
            perimeter = calc_perimeter((*continuos_ring_positions)[ring_id]);
        } else {
            perimeter = calc_continuos_pos(ring_id);
        }

        // pos_continuos[ring_id][0] = pos[ring_id][0];
        // for (size_t i = 0; i < (differences[ring_id].size()-1); i++)
        // {
        //     pos_continuos[ring_id][i+1][0] = pos_continuos[ring_id][i][0] + differences[ring_id][i][0];
        //     pos_continuos[ring_id][i+1][1] = pos_continuos[ring_id][i][1] + differences[ring_id][i][1];
        // }

        double area = calc_area((*continuos_ring_positions)[ring_id]);
        
        #if DEBUG
        area_debug.area[ring_id] = area;
        #endif

        for (size_t i = 0; i < (*continuos_ring_positions)[ring_id].size(); i++)
        {
            format_force(ring_id, i, area, perimeter);
        }
    }

    void target_perimeter_forces(int ring_id) {
        double perimeter = calc_continuos_pos(ring_id);

        #if DEBUG
        double area = calc_area(pos_continuos[ring_id]);
        area_debug.area[ring_id] = area;
        #endif

        // auto& ring_pos = pos[ring_id];
        for (int i = 0; i < num_particles; i++)
        {
            double d1 = vector_mod(differences[ring_id][i]);
            
            int id2 = i-1;
            if (i == 0)
                id2 = num_particles - 1;
            double d2 = vector_mod(differences[ring_id][id2]);
            
            double  force_k = k_area * (perimeter - p_target);

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
        if ((update_type == RingUpdateType::periodic_borders) || 
            (update_type == RingUpdateType::invagination)) {
            calc_continuos_pos(ring_id);
        }

        double area = calc_area((*continuos_ring_positions)[ring_id]);
        #if DEBUG
        area_debug.area[ring_id] = area;
        #endif

        auto& ring_pos = pos[ring_id];
        int id1, id2;
        for (int i = 0; i < num_particles; i++)
        {
            double force_k = k_area * (area - area0);

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

    void collision_forces() {
        for (int col_id = 0; col_id < in_pol_checker.num_collisions; col_id++)
        {
            if (in_pol_checker.is_col_resolved[col_id] == true) {
                continue;
            } 

            auto& col_info = in_pol_checker.collisions[col_id];
            auto& ring_pos = pos[col_info.ring_id];
            auto& p = ring_pos[col_info.p_id];
                    
            if (in_pol_checker.is_inside_pol(p[0], p[1], col_info.col_ring_id) == false) {
                in_pol_checker.is_col_resolved[col_id] = true;
                resolved_invs.add_collision(col_info);
                continue;
            }

            
            // auto& ring_cm = center_mass[col_info.col_ring_id];
            // double radius_vec = {p[0] - ring_cm[0], p[1] - ring_cm[1]};
            // double norm = vector_mod(radius_vec)
            // double dx = p[0] - ring_cm[0];
            // double dy = p[1] - ring_cm[1];
            // double norm = periodic_dist(dx, dy);
            
            int after_p_id = col_info.p_id == (num_particles-1) ? 0 : col_info.p_id + 1; 
            int before_p_id = col_info.p_id == 0 ? (num_particles - 1) : col_info.p_id - 1; 
            
            double dx = -(ring_pos[after_p_id][1] - ring_pos[before_p_id][1]);
            double dy = (ring_pos[after_p_id][0] - ring_pos[before_p_id][0]);
            double norm = periodic_dist(dx, dy);

            // double sign = -area_debug.area[col_info.ring_id] + area0;
            // sign = -sign/sign;
            
            // double dx = sign * area_forces[col_info.ring_id][col_info.p_id][0];
            // double dy = sign * area_forces[col_info.ring_id][col_info.p_id][1];
            // double norm = sqrt(dx*dx + dy*dy);
            
            double fx = dx/norm * k_invasion;
            double fy = dy/norm * k_invasion;

            #if DEBUG == 1
            invasion_forces[col_info.ring_id][col_info.p_id][0] = fx;
            invasion_forces[col_info.ring_id][col_info.p_id][1] = fy;
            #endif

            sum_forces_matrix[col_info.ring_id][col_info.p_id][0] += fx;
            sum_forces_matrix[col_info.ring_id][col_info.p_id][1] += fy;
        }

        vector<size_t> ids_to_remove;
        int count = 0;
        for (auto& inv_i : resolved_invs.invasions) {
            if (inv_i.num_steps_elapsed > steps_after_resolved) {
                ids_to_remove.push_back(count);
                continue;
            }

            auto& col_info = inv_i.col;
            auto& ring_pos = pos[col_info.ring_id];

            int after_p_id = col_info.p_id == (num_particles-1) ? 0 : col_info.p_id + 1; 
            int before_p_id = col_info.p_id == 0 ? (num_particles - 1) : col_info.p_id - 1; 
            
            double dx = -(ring_pos[after_p_id][1] - ring_pos[before_p_id][1]);
            double dy = (ring_pos[after_p_id][0] - ring_pos[before_p_id][0]);
            double norm = periodic_dist(dx, dy);

            double fx = dx/norm * k_invasion;
            double fy = dy/norm * k_invasion;

            #if DEBUG == 1
            invasion_forces[col_info.ring_id][col_info.p_id][0] = fx;
            invasion_forces[col_info.ring_id][col_info.p_id][1] = fy;
            #endif

            sum_forces_matrix[col_info.ring_id][col_info.p_id][0] += fx;
            sum_forces_matrix[col_info.ring_id][col_info.p_id][1] += fy;

            count += 1;
            inv_i.num_steps_elapsed += 1;
        }

        if (ids_to_remove.size() > 0) {
            resolved_invs.remove_ids(ids_to_remove);
        }
    }

    void calc_forces_normal(int ring_id) {
        // Excluded volume
        for (int p_id = 0; p_id < num_particles; p_id ++) {
            for (int other_ring_id = 0; other_ring_id < num_max_rings; other_ring_id++)
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
            calc_format_forces(ring_id);
            break;
        case AreaPotencialType::target_perimeter:
            target_perimeter_forces(ring_id);
            break;
        case AreaPotencialType::target_area:
            target_area_forces(ring_id);
            break;
        case AreaPotencialType::target_area_and_format:
            calc_format_forces(ring_id);
            target_area_forces(ring_id);
            break;
        }
    }

    void calc_forces_windows() {
        #if DEBUG == 1
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++) {
        for (int i = 0; i < num_active_rings; i++) 
        {
            int ring_id = rings_ids[i];
            for (int i = 0; i < num_particles; i++) {
                spring_forces[ring_id][i][0] = 0.;
                spring_forces[ring_id][i][1] = 0.;
                
                vol_forces[ring_id][i][0] = 0.;
                vol_forces[ring_id][i][1] = 0.;
                
                obs_forces[ring_id][i][0] = 0.;
                obs_forces[ring_id][i][1] = 0.;
                
                invasion_forces[ring_id][i][0] = 0.;
                invasion_forces[ring_id][i][1] = 0.;
            }
        }
        #endif

        // Excluded volume
        #pragma omp parallel for schedule(dynamic, 15)
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

        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        #pragma omp parallel for schedule(dynamic, 10)
        for (int i = 0; i < num_active_rings; i++) 
        {
            int ring_id = rings_ids[i];

            // Springs
            // for (int p_id = 0; p_id < num_particles; p_id ++) {
            //     int id_left = (p_id == 0) ? num_particles-1 : p_id-1;
            //     int id_right = (p_id == num_particles-1) ? 0 : p_id+1;

            //     calc_spring_force(ring_id, p_id, id_left);
            //     calc_spring_force(ring_id, p_id, id_right);

            //     // Flux force
            //     if (update_type == RingUpdateType::stokes) {
            //         if (pos[ring_id][p_id][0] < max_create_border) {
            //             sum_forces_matrix[ring_id][p_id][0] += stokes_cfg.flux_force;
            //         }
            //     }
            // }
            for (int spring_id = 0; spring_id < num_particles; spring_id++)
            {
                calc_spring_force2(ring_id, spring_id);
                
                if (update_type == RingUpdateType::stokes) {
                    Vec2d& p_pos = pos[ring_id][spring_id];
                    
                    // Flux force
                    if (p_pos[0] < max_create_border) {
                        sum_forces_matrix[ring_id][spring_id][0] += stokes_cfg.flux_force;
                    }
                    
                    // Obstacle force
                    double dx = p_pos[0] - stokes_cfg.obstacle_x;
                    double dy = p_pos[1] - stokes_cfg.obstacle_y;
                    Vec2d radius_pos = {dx, dy};

                    double radius = sqrt(dx * dx + dy * dy);
                    if (radius < stokes_cfg.obstacle_r ) {
                        double obs_force_x = radius_pos[0]/radius * stokes_cfg.obs_force;
                        double obs_force_y = radius_pos[1]/radius * stokes_cfg.obs_force;

                        sum_forces_matrix[ring_id][spring_id][0] += obs_force_x;
                        sum_forces_matrix[ring_id][spring_id][1] += obs_force_y;

                        #if DEBUG == 1
                        obs_forces[ring_id][spring_id][0] = obs_force_x;
                        obs_forces[ring_id][spring_id][1] = obs_force_y;
                        #endif
                    }
                }
            }
            
            // Bend
            switch (dynamic_cfg.area_potencial)
            {
            case AreaPotencialType::format:
                calc_format_forces(ring_id);
                break;
            case AreaPotencialType::target_perimeter:
                target_perimeter_forces(ring_id);
                break;
            case AreaPotencialType::target_area:
                target_area_forces(ring_id);
                break;
            case AreaPotencialType::target_area_and_format:
                target_area_forces(ring_id);
                calc_format_forces(ring_id);
                break;
            }
        }

        collision_forces();
    }

    void stokes_resolve_collisions(Vec2d& p_pos, Vec2d& p_vel) {
        //
        // Colisões com as paredes
        //
        if (p_pos[1] > height/2.) {
            if (p_vel[1] > 0.0) 
                p_vel[1] = 0.0;
        }
        else if (p_pos[1] < -height/2.) {
            if (p_vel[1] < 0.0)
                p_vel[1] = 0.0;
        }
        
        if ((p_pos[0] < -length/2.) && (p_vel[0] < 0.0))
            p_vel[0] = 0.0f;

        //
        // Colisões com o obstáculo
        //
        // double dx = p_pos[0] - stokes_cfg.obstacle_x;
        // double dy = p_pos[1] - stokes_cfg.obstacle_y;
        // Vec2d radius_pos = {dx, dy};

        // double radius_sqr = dx * dx + dy * dy;
        // if (radius_sqr < (stokes_cfg.obstacle_r * stokes_cfg.obstacle_r)) {
        //     double dot_pos_vel = dot_prod(radius_pos, p_vel);

        //     if (dot_pos_vel < 0.0) {
        //         // double pos_length = sqrt(radius_sqr);

        //         p_vel[0] -= radius_pos[0]/(radius_sqr)*dot_pos_vel;
        //         p_vel[1] -= radius_pos[1]/(radius_sqr)*dot_pos_vel;
        //     }
        // }
    }

    void calc_derivate(double &vel_x, double &vel_y, Vec2d self_vel_i, int ring_id, int particle_id) {
        int i = particle_id;

        #if DEBUG == 1    
            auto& rng_nums = rng_manager.get_random_num(i, ring_id);
            double rng_trans_x = (double)rng_nums[1]/(double)RAND_MAX * 2. - 1.;
            double rng_trans_y = (double)rng_nums[2]/(double)RAND_MAX * 2. - 1.;
        #else
            double rng_trans_x = (double)rand()/(double)RAND_MAX * 2. - 1.;
            double rng_trans_y = (double)rand()/(double)RAND_MAX * 2. - 1.;
        #endif
        double noise_trans_x = rng_trans_x * sqrt(2. * trans_diff) / sqrt(dt); 
        double noise_trans_y = rng_trans_y * sqrt(2. * trans_diff) / sqrt(dt); 
        
        double vel_x_i = vo * self_vel_i[0] + mobility * sum_forces_matrix[ring_id][i][0] + noise_trans_x;
        double vel_y_i = vo * self_vel_i[1] + mobility * sum_forces_matrix[ring_id][i][1] + noise_trans_y;
        Vec2d vel_i = {vel_x_i, vel_y_i};

        if (update_type == RingUpdateType::stokes)
            stokes_resolve_collisions(pos[ring_id][particle_id], vel_i);

        #if DEBUG == 1
        double speed = sqrt(vel_i[0]*vel_i[0] + vel_i[1] * vel_i[1]);
        if (speed > 1e6) {
            update_debug.high_vel = true;
            std::cout << "Error: High velocity" << std::endl;
        }
        #endif
        
        vel[ring_id][particle_id] = vel_i;  

        vel_x = vel_i[0];
        vel_y = vel_i[1];
    }

    double self_angle_derivate(Vec2d self_vel, double ring_id) {
        // Velocidade do centro de massa
        Vec2d cm_vel = {0.0, 0.0};
        for (int i = 0; i < num_particles; i++)
        {
            cm_vel[0] += vel[ring_id][i][0];
            cm_vel[1] += vel[ring_id][i][1];
        }
        cm_vel[0] /= (double)num_particles;
        cm_vel[1] /= (double)num_particles;
    
        double speed = vector_mod(cm_vel);

        // Geração do ruíno rotacional
        #if DEBUG == 1    
            auto& rng_nums = rng_manager.get_random_num(0, ring_id);
            double rng_rot = (double)rng_nums[0]/(double)RAND_MAX * 2. - 1.;
        #else
            double rng_rot = (double)rand()/(double)RAND_MAX * 2. - 1.;
        #endif
        double noise_rot = rng_rot * sqrt(2. * rot_diff) / sqrt(dt); 
        
        // Derivada do ângulo da velocidade auto propulsora
        double angle_derivate;
        if (speed == 0.0) {
            update_debug.count_zero_speed += 1;
            angle_derivate = 0.;
        } else {
            double cross_prod = self_vel[0] * cm_vel[1]/speed - self_vel[1] * cm_vel[0]/speed;
            
            if (abs(cross_prod) > 1) {
                #if DEBUG == 1
                std::cout << "Error: cross_prod | " << cross_prod << std::endl;
                #endif
                cross_prod = copysign(1, cross_prod);
            }

            angle_derivate = 1. / relax_time * asin(cross_prod) + noise_rot;
        }

        return angle_derivate;
    }

    void advance_time() {
        Vec2d vel_i;

        #pragma omp parallel for schedule(dynamic, 10)
        for (int i = 0; i < num_active_rings; i++)
        {
            int ring_id = rings_ids[i];
            Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
            for (int i=0; i < num_particles; i++) {
                calc_derivate(vel_i[0], vel_i[1], self_vel_i, ring_id, i);

                pos[ring_id][i][0] += vel_i[0] * dt;
                pos[ring_id][i][1] += vel_i[1] * dt;

                #if DEBUG == 1
                if (isnan(pos[ring_id][i][0]) == true) {
                    std::cout << "Error: pos nan 1" << std::endl;
                }
                #endif

                periodic_border(pos[ring_id][i]);

                #if DEBUG == 1
                if (isnan(pos[ring_id][i][0]) == true)
                    std::cout << "Error: pos_nan 2" << std::endl;

                total_forces[ring_id][i][0] = sum_forces_matrix[ring_id][i][0];
                total_forces[ring_id][i][1] = sum_forces_matrix[ring_id][i][1];
                #endif

                sum_forces_matrix[ring_id][i][0] = 0.f;
                sum_forces_matrix[ring_id][i][1] = 0.f;
            }        

            double angle_deriv = self_angle_derivate(self_vel_i, ring_id);
            self_prop_angle[ring_id] += angle_deriv * dt;
        }
    }

    void advance_time_stokes() {
        Vec2d vel_i;

        #pragma omp parallel for schedule(dynamic, 10)
        for (int i = 0; i < num_active_rings; i++)
        {
            int ring_id = rings_ids[i];
            Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
            for (int i=0; i < num_particles; i++) {
                calc_derivate(vel_i[0], vel_i[1], self_vel_i, ring_id, i);
                
                pos[ring_id][i][0] += vel_i[0] * dt;
                pos[ring_id][i][1] += vel_i[1] * dt;

                #if DEBUG == 1
                if (isnan(pos[ring_id][i][0]) == true) {
                    std::cout << "Error: pos nan 1" << std::endl;
                }

                total_forces[ring_id][i][0] = sum_forces_matrix[ring_id][i][0];
                total_forces[ring_id][i][1] = sum_forces_matrix[ring_id][i][1];
                #endif

                sum_forces_matrix[ring_id][i][0] = 0.f;
                sum_forces_matrix[ring_id][i][1] = 0.f;
            }        
            
            if (center_mass[ring_id][0] > remove_border) {
                remove_ring(ring_id);
            } else {
                double angle_deriv = self_angle_derivate(self_vel_i, ring_id);
                self_prop_angle[ring_id] += angle_deriv * dt;
            }
        }

        if (to_recalculate_ids == true) {
            recalculate_rings_ids();
        }
    }

    void advance_time_verlet() {
        std::cout << "Esse método está desatualizado!" << std::endl;
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
        //     for (int i=0; i < num_particles; i++) {
        //         auto& vel_x = k_matrix[0][ring_id][i][0];
        //         auto& vel_y = k_matrix[0][ring_id][i][1];
        //         auto& angle_deriv_i = k_matrix[0][ring_id][i][2];

        //         #if DEBUG == 1
        //         if (isnan(vel_x) == true) {
        //             std::cout << "Error: vel nan 1" << std::endl;
        //         }
        //         #endif
                
        //         calc_derivate(vel_x, vel_y, angle_deriv_i, self_vel_i, ring_id, i);

        //         #if DEBUG == 1
        //         if (isnan(vel_x) == true) {
        //             std::cout << "Error: vel nan 2" << std::endl;
        //         }
        //         #endif

        //         old_pos[ring_id][i][0] = pos[ring_id][i][0];
        //         old_pos[ring_id][i][1] = pos[ring_id][i][1];
        //         old_self_prop_angle[ring_id][i] = self_prop_angle[ring_id][i];
                
        //         pos[ring_id][i][0] += vel_x * dt;
        //         pos[ring_id][i][1] += vel_y * dt;
        //         self_prop_angle[ring_id][i] += angle_deriv_i * dt;

        //         #if DEBUG == 1
        //         if (isnan(pos[ring_id][i][0]) == true) {
        //             std::cout << "Error: pos nan 1" << std::endl;
        //         }
        //         #endif

        //         periodic_border(pos[ring_id][i]);

        //         // for (int dim = 0; dim < 2.f; dim ++) {
        //         //     if (pos[ring_id][i][dim] > height/2.f)
        //         //         pos[ring_id][i][dim] -= height;
        //         //     else if (pos[ring_id][i][dim] < -height/2.f)
        //         //         pos[ring_id][i][dim] += height;
        //         // }

        //         #if DEBUG == 1
        //         if (isnan(pos[ring_id][i][0]) == true)
        //             std::cout << "Error: pos_nan 2" << std::endl;
        //         #endif

        //         sum_forces_matrix[ring_id][i][0] = 0.f;
        //         sum_forces_matrix[ring_id][i][1] = 0.f;
        //     } 
        // }
        
        // calc_forces_windows();

        // double angle_deriv_2;
        // Vec2d vel2;
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
        //     for (int i=0; i < num_particles; i++) {
        //         calc_derivate(vel2[0], vel2[1], angle_deriv_2, self_vel_i, ring_id, i);
                
        //         auto& old_pos_i = old_pos[ring_id][i];
        //         auto& old_angle_i = old_self_prop_angle[ring_id][i];

        //         auto& k1 = k_matrix[0][ring_id][i];
        //         Vec2d vel1 = {k1[0], k1[1]};
        //         auto angle_deriv_1 = k1[2];

        //         pos[ring_id][i][0] = old_pos_i[0] + 0.5 * (vel1[0] + vel2[0]) * dt;
        //         pos[ring_id][i][1] = old_pos_i[1] + 0.5 * (vel1[1] + vel2[1]) * dt;
        //         self_prop_angle[ring_id][i] = old_angle_i + 0.5 * (angle_deriv_1 + angle_deriv_2) * dt;

        //         if (isnan(pos[ring_id][i][0]) == true) {
        //             std::cout << "Error: pos nan 1" << std::endl;
        //         }
                
        //         periodic_border(pos[ring_id][i]);
        
        //         // for (int dim = 0; dim < 2.f; dim ++) {
        //         //     if (pos[ring_id][i][dim] > height/2.f)
        //         //         pos[ring_id][i][dim] -= height;
        //         //     else if (pos[ring_id][i][dim] < -height/2.f)
        //         //         pos[ring_id][i][dim] += height;
        //         // }

        //         #if DEBUG == 1
        //         if (isnan(pos[ring_id][i][0]) == true)
        //             std::cout << "Error: pos_nan 2" << std::endl;

        //         total_forces[ring_id][i][0] = sum_forces_matrix[ring_id][i][0];
        //         total_forces[ring_id][i][1] = sum_forces_matrix[ring_id][i][1];
        //         #endif

        //         sum_forces_matrix[ring_id][i][0] = 0.f;
        //         sum_forces_matrix[ring_id][i][1] = 0.f;
        //     }
        // }
    }

    void advance_time_rk4() {
        std::cout << "Esse método está desatualizado!" << std::endl;
        // if (is_low_dt == true) {
        //     dt_count ++;

        //     if (dt_count > num_low_dt) {
        //         is_low_dt = false;
        //         dt = base_dt;
        //     }
        // }

        // if (is_low_dt == false) {
        //     double max_force = 0;
        //     for (int ring_id = 0; ring_id < num_max_rings; ring_id++) {
        //         for (auto& f: total_forces[ring_id]) {
        //             double f_mod = vector_mod(f);
        //             if (f_mod > max_force) {
        //                 max_force = f_mod;
        //             }
        //         }
        //     }
            
        //     // std::cout << "Max Force: " << max_force << std::endl;

        //     if (max_force > 15) {
        //         dt = low_dt;
        //         is_low_dt = true;
        //         dt_count = 0;
        //     }
        // }

        
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     for (int p_id = 0; p_id < num_particles; p_id++)
        //     {
        //         old_pos[ring_id][p_id][0] = pos[ring_id][p_id][0];
        //         old_pos[ring_id][p_id][1] = pos[ring_id][p_id][1];
        //         old_self_prop_angle[ring_id][p_id] = self_prop_angle[ring_id][p_id];
        //     }
        // }
        
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
        //     for (int i=0; i < num_particles; i++) {
        //         double& vel_i_x = k_matrix[0][ring_id][i][0];
        //         double& vel_i_y = k_matrix[0][ring_id][i][1];
        //         double& angle_deriv_i = k_matrix[0][ring_id][i][2];

        //         calc_derivate(vel_i_x, vel_i_y, angle_deriv_i, self_vel_i, ring_id, i);

        //         pos[ring_id][i][0] += vel_i_x * dt * 0.5;
        //         pos[ring_id][i][1] += vel_i_y * dt * 0.5;
        //         self_prop_angle[ring_id][i] += angle_deriv_i * dt * 0.5;

        //         periodic_border(pos[ring_id][i]);
        //         // for (int dim = 0; dim < 2.f; dim ++) {
        //         //     if (pos[ring_id][i][dim] > height/2.f)
        //         //         pos[ring_id][i][dim] -= height;
        //         //     else if (pos[ring_id][i][dim] < -height/2.f)
        //         //         pos[ring_id][i][dim] += height;
        //         // }

        //         sum_forces_matrix[ring_id][i][0] = 0.f;
        //         sum_forces_matrix[ring_id][i][1] = 0.f;
        //     } 
        // }
        // calc_forces_windows();
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
        //     for (int i=0; i < num_particles; i++) {
        //         double& vel_i_x = k_matrix[1][ring_id][i][0];
        //         double& vel_i_y = k_matrix[1][ring_id][i][1];
        //         double& angle_deriv_i = k_matrix[1][ring_id][i][2];

        //         calc_derivate(vel_i_x, vel_i_y, angle_deriv_i, self_vel_i, ring_id, i);

        //         pos[ring_id][i][0] = old_pos[ring_id][i][0] + vel_i_x * dt * 0.5;
        //         pos[ring_id][i][1] = old_pos[ring_id][i][1] + vel_i_y * dt * 0.5;
        //         self_prop_angle[ring_id][i] = old_self_prop_angle[ring_id][i] + angle_deriv_i * dt * 0.5;

        //         periodic_border(pos[ring_id][i]);
        //         // for (int dim = 0; dim < 2.f; dim ++) {
        //         //     if (pos[ring_id][i][dim] > height/2.f)
        //         //         pos[ring_id][i][dim] -= height;
        //         //     else if (pos[ring_id][i][dim] < -height/2.f)
        //         //         pos[ring_id][i][dim] += height;
        //         // }

        //         sum_forces_matrix[ring_id][i][0] = 0.f;
        //         sum_forces_matrix[ring_id][i][1] = 0.f;
        //     } 
        // }
        // calc_forces_windows();
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
        //     for (int i=0; i < num_particles; i++) {
        //         double& vel_i_x = k_matrix[2][ring_id][i][0];
        //         double& vel_i_y = k_matrix[2][ring_id][i][1];
        //         double& angle_deriv_i = k_matrix[2][ring_id][i][2];

        //         calc_derivate(vel_i_x, vel_i_y, angle_deriv_i, self_vel_i, ring_id, i);

        //         pos[ring_id][i][0] = old_pos[ring_id][i][0] + vel_i_x * dt;
        //         pos[ring_id][i][1] = old_pos[ring_id][i][1] + vel_i_y * dt;
        //         self_prop_angle[ring_id][i] = old_self_prop_angle[ring_id][i] + angle_deriv_i * dt;

        //         periodic_border(pos[ring_id][i]);
        //         // for (int dim = 0; dim < 2.f; dim ++) {
        //         //     if (pos[ring_id][i][dim] > height/2.f)
        //         //         pos[ring_id][i][dim] -= height;
        //         //     else if (pos[ring_id][i][dim] < -height/2.f)
        //         //         pos[ring_id][i][dim] += height;
        //         // }

        //         sum_forces_matrix[ring_id][i][0] = 0.f;
        //         sum_forces_matrix[ring_id][i][1] = 0.f;
        //     } 
        // }
        // calc_forces_windows();
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     Vec2d self_vel_i = {cos(self_prop_angle[ring_id]), sin(self_prop_angle[ring_id])};
        //     for (int i=0; i < num_particles; i++) {
        //         double& vel_i_x = k_matrix[3][ring_id][i][0];
        //         double& vel_i_y = k_matrix[3][ring_id][i][1];
        //         double& angle_deriv_i = k_matrix[3][ring_id][i][2];

        //         calc_derivate(vel_i_x, vel_i_y, angle_deriv_i, self_vel_i, ring_id, i);
        //         sum_forces_matrix[ring_id][i][0] = 0.f;
        //         sum_forces_matrix[ring_id][i][1] = 0.f;
        //     } 
        // }
        
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++)
        // {
        //     for (int i=0; i < num_particles; i++) {
        //         auto& k1 = k_matrix[0][ring_id][i];
        //         auto& k2 = k_matrix[1][ring_id][i];
        //         auto& k3 = k_matrix[2][ring_id][i];
        //         auto& k4 = k_matrix[3][ring_id][i];

        //         pos[ring_id][i][0] = old_pos[ring_id][i][0] + dt * (1./6. * k1[0] + 1./3. * k2[0] + 1./3. * k3[0] + 1./6. * k4[0]);
        //         pos[ring_id][i][1] = old_pos[ring_id][i][1] + dt * (1./6. * k1[1] + 1./3. * k2[1] + 1./3. * k3[1] + 1./6. * k4[1]);
        //         self_prop_angle[ring_id][i] = old_self_prop_angle[ring_id][i] + dt * (1./6. * k1[2] + 1./3. * k2[2] + 1./3. * k3[2] + 1./6. * k4[2]);

        //         periodic_border(pos[ring_id][i]);
        //         // for (int dim = 0; dim < 2.f; dim ++) {
        //         //     if (pos[ring_id][i][dim] > height/2.f)
        //         //         pos[ring_id][i][dim] -= height;
        //         //     else if (pos[ring_id][i][dim] < -height/2.f)
        //         //         pos[ring_id][i][dim] += height;
        //         // }
        //     } 
        // }
    }

    void update_normal() {
        #if DEBUG == 1
        rng_manager.update();
        #endif

        for (int ring_id = 0; ring_id < num_max_rings; ring_id++) {
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
        case RingIntegrationType::euler:
            advance_time();
            break;
        case RingIntegrationType::verlet:
            advance_time_verlet();
            break;
        case RingIntegrationType::rk4:
            advance_time_rk4();
            break;
        }
        
        #if DEBUG == 1
        update_graph_points();   
        #endif

        sim_time += dt;
        num_time_steps += 1;
    }

    void update_windows() {
        #if DEBUG == 1
        rng_manager.update();
        #endif

        // if (sim_time > 5.0) {
        //     add_ring();
        // }
        
        // if (sim_time > 10.0) {
        //     remove_ring(0);
        // }

        if (to_recalculate_ids == true)
            recalculate_rings_ids();

        windows_manager.update_window_members();

        in_pol_checker.update();
        
        calc_center_mass();
        
        calc_forces_windows();

        switch (integration_type)
        {
        case RingIntegrationType::euler:
            advance_time();
            break;
        case RingIntegrationType::verlet:
            advance_time_verlet();
            break;
        case RingIntegrationType::rk4:
            advance_time_rk4();
            break;
        }

        #if DEBUG == 1
        update_graph_points();   
        #endif

        sim_time += dt;
        num_time_steps += 1;
    }

    void update_stokes() {
        #if DEBUG == 1
        rng_manager.update();

        int ring_id;
        for (int i = 0; i < num_active_rings; i++) {
            ring_id = rings_ids[i];
            calc_differences(ring_id);
        }
        #endif

        // bool crete_new_ring = true;
        // for (auto win_id: begin_windows_ids) {
        //     int num_win_rings = windows_manager.capacity[win_id[0]][win_id[1]];

        //     if (num_win_rings > 0) {
        //         crete_new_ring = false;
        //         break;
        //     }
        // }
        // bool crete_new_ring = true;
        // 
        // if (crete_new_ring == true)
        //     add_ring();
        
        // std::cout << "Criando novos aneis" << std::endl;
        for (size_t i = 0; i < create_rings_win_ids.size(); i++)
        {
            // std::cout << "Anel id:" << i << std::endl;
            auto& ring_window_ids = create_rings_win_ids[i];
            bool create_new_ring = true;
            for (auto& win_id: ring_window_ids) {
                int num_win_rings = windows_manager.capacity[win_id[0]][win_id[1]];
                
                // auto& win_center =  windows_manager.windows_center[win_id[0]][win_id[1]];
                // std::cout << "Janela centro:" << win_center[0] << ", " << win_center[1] << std::endl;
                // std::cout << "Num inside:" << num_win_rings << std::endl;
                
                if (num_win_rings > 0) {
                    create_new_ring = false;
                    break;
                }
            }
            // std::cout << "========" << std::endl;

            to_create_new_ring[i] = create_new_ring;
        }

        num_created_rings = 0;
        for (size_t i = 0; i < to_create_new_ring.size(); i++) {
            if (to_create_new_ring[i] == true) {
                num_created_rings += 1;
                add_ring(i);
            }
        }
        
        if (to_recalculate_ids == true) {
            // std::cout << "Recalculando ids" << std::endl;
            recalculate_rings_ids();
        }

        // std::cout << "Atualizando janelas (particulas)" << std::endl;
        windows_manager.update_window_members();
        
        // std::cout << "\n#== Janelas ==#" << std::endl;
        // for (auto& wid: windows_manager.windows_ids) {
        //     auto& win_center = windows_manager.windows_center[wid[0]][wid[1]];
        //     if (win_center[0] < -54) {
        //         std::cout << "Janela centro:" << win_center[0] << ", " << win_center[1] << std::endl;
        //         std::cout << "num_inside:" << windows_manager.capacity[wid[0]][wid[1]] << std::endl;
        //         std::cout << "====" << std::endl;
        //     }
        // }
        // std::cout << "#======#\n" << std::endl;

        // std::cout << "Atualizando janelas (CM)" << std::endl;
        in_pol_checker.windows_manager.update_window_members();    
        // std::cout << "Atualizando janelas InPolChecker" << std::endl;
        in_pol_checker.update();

        // std::cout << "Calculando forças" << std::endl;
        calc_forces_windows();
        // Obstacle force


        // std::cout << "Calculando CM" << std::endl;
        calc_center_mass();
        
        // std::cout << "Avançando no tempo" << std::endl;
        advance_time_stokes();

        #if DEBUG == 1
        update_graph_points();   
        #endif

        sim_time += dt;
        num_time_steps += 1;
    }

    void update_visual_aids() {
        windows_manager.update_window_members();

        calc_forces_windows();
        
        calc_center_mass();
        in_pol_checker.update();
        
        update_graph_points();   
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
        if (abs(dx) > length * 0.5) {
            calc_intersect = true;
            dx -= copysign(length, dx);
        }
        if (abs(dy) > height * 0.5) {
            calc_intersect = true;
            dy -= copysign(height, dy);
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
        // for (int ring_id = 0; ring_id < num_max_rings; ring_id++) {
        for (int i = 0; i < num_active_rings; i++) 
        {
            int ring_id = rings_ids[i];

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
};