#version 330 core

layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aColor;

out vec3 ourColor;

uniform float offset = 0;    

void transform(inout float value) {
    value = (value + 1.0f) / 2.0f;
} 

void transformVec(inout vec3 value) {
    transform(value.x);
    transform(value.y);
    transform(value.z);
}

void main() {
    gl_Position = vec4(aPos.x + offset, aPos.yz, 1.0f);
    ourColor = gl_Position.xyz;
    transformVec(ourColor);
}