#pragma once

#include <array>
#include <cmath>

using namespace std;

class IntersectionCalculator {
/** 
 * Calcula os pontos de intersecção de uma linha com um quadrado. 
 */

public:
    double size; // Lado do quadrado
    
    IntersectionCalculator() { };
    IntersectionCalculator(double size): size(size) { };

    void calc_points(array<double, 2> &p1, array<double, 2> &p2, array<array<double, 2>, 2> &intersect) {
        /**
         * Calcula os pontos de intersecção para a linha definida pelos pontos 'p1' e 'p2' 
         * e os coloca em 'intersect'.
         * 
         * Notes
         * -----
         * Dado a equação de uma reta
         * 
         *      ax + by = c
         * 
         * São calculados os coeficientes a, b e c da reta definida por 'p1' e 'p2', então,
         * são calculados os pontos de intersecção com as retas
         *      
         *      x = -size/2
         *      x = +size/2
         *      y = -size/2
         *      y = +size/2
         * 
         * Desses 4 pontos de intersecção, é verificados quais são os dois pontos
         * que pertencem a intersecção da reta com o quadrado. 
         * 
         * OBS: Os casos em que a=0 ou b=0 são triviais e lidados separadamente.
         *      Caso a=0 e b=0 é considerado que a reta é vertical.
         */
        double dx = p1[0] - p2[0];
        double dy = p1[1] - p2[1];

        double a, b, c;
        if (dx == 0) {
            a = 1.;
            b = 0.;
            c = p1[0];
        } else {
            double m = dy/dx;
            a = -m;
            b = 1.;
            c = p1[1] - p1[0] * m;
        }

        if (a == 0) {
            intersect[0][0] = -size/2.;
            intersect[0][1] = c/b;
            
            intersect[1][0] = -intersect[0][0];
            intersect[1][1] = intersect[0][1];
        } else if (b == 0) {
            intersect[0][0] = c/a;
            intersect[0][1] = -size/2.;
            
            intersect[1][0] = intersect[0][0];
            intersect[1][1] = -intersect[0][1];
        } else {
            // Coordenada y dos pontos de intersecção com x=+-size/2
            double x1_ycoord = c +  a * size / 2.;
            double x2_ycoord = c -  a * size / 2.;
            
            // Coordenada x dos pontos de intersecção com y=+-size/2
            double y1_xcoord = (c + size / 2.) / a;
            double y2_xcoord = (c - size / 2.) / a;
            
            array<double, 4> coord_test = {x1_ycoord, x2_ycoord, y1_xcoord, y2_xcoord};
            array<int, 4> coord_id = {0, 0, 1, 1}; // 0: linha vertical, 1: linha horizontal
            array<int, 4> sinal = {-1, 1, -1, 1};

            int num_points = 0;
            int count = 0;
            while (num_points < 2) {
                double coord = coord_test[count];

                // Condição para que o ponto seja da intersecção do quadrado.
                if (abs(coord) <= size/2.) {
                    double x, y;
                    if (coord_id[count] == 0) {
                        x = size / 2 * sinal[count];
                        y = coord;
                    } else {
                        x = coord;
                        y = size / 2 * sinal[count];
                    }
                    intersect[num_points][0] = x;
                    intersect[num_points][1] = y;
                    num_points += 1;
                }
                count += 1;
            }
        }
    }
};