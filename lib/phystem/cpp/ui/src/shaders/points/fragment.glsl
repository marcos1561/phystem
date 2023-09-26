#version 330 core

out vec4 fragColor;

uniform vec3 color = vec3(1.0f, 1.0f, 0.0f);

void main() {
    fragColor = vec4(color.xyz, 1.0f);
}