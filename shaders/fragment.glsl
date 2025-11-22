#version 330
in vec2 uv;

out vec4 FragColor;

uniform float u_time;
void main() {
    FragColor = vec4(sin(u_time)*uv.y/2.0, cos(u_time)*uv.x/2.0, sin(u_time), 1.0);
}

