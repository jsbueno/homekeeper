#include "colors.inc"

#include "ball_parameters.inc"
// #declare strype_color = color rgb <1, 1, 0>;

camera {

    location <0, 0, -3>
    look_at 0
    right <1, 0, 0>


}

sphere {
    0, 1
    texture {
        pigment {
            radial
            color_map {
                [0.02 Black]
                [0.02 White]
                [0.52 White]
                [0.52 Black]
                [0.54 Black]
                [0.54 strype_color]
            }
            frequency 4
        }
    }
    texture {
        pigment {
            gradient <0, 1, 0>
            color_map {
                [0.45 color rgbt<1, 1, 1, 1>]
                [0.45 color rgbt<1, 0, 0, 0>]
                [0.55 color rgbt<1, 0, 0, 0>]
                [0.55 color rgbt<1, 1, 1, 1>]
                [0.975 color rgbt<1, 1, 1, 1>]
                [0.975 color Black]
            }
            translate <0, -.5, 0>
            scale 2
        }
        finish {
            ambient 0.3
            specular 0.6
            roughness 0.05
        }
    }
    rotate <-35, 15, 0>
}


light_source {
    <-3, 3, -3>
    color White
}

light_source {
    <3, -3, -3>
    color White * 0.3
}

