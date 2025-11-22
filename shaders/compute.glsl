#version 430

// Define work group size - these will be replaced by the Python code
layout(local_size_x=COMPUTE_SIZE_X, local_size_y=COMPUTE_SIZE_Y) in;

// Output image
layout(rgba32f, binding=0) uniform writeonly image2D output_image;

// Uniforms that can be passed from Python
uniform float u_time = 0.0;
uniform vec2 u_resolution = vec2(800.0, 600.0);

void main()
{
    // Get the pixel coordinates
    ivec2 pixel_coords = ivec2(gl_GlobalInvocationID.xy);

    // Check if within bounds
    if (pixel_coords.x >= u_resolution.x || pixel_coords.y >= u_resolution.y) {
        return;
    }

    // Calculate normalized coordinates (0.0 to 1.0)
    vec2 uv = vec2(pixel_coords) / u_resolution;

    // Create an animated pattern
    float r = sin(uv.x + u_time) * 0.5 + 0.5;
    float g = sin(uv.y + u_time * 1.2) * 0.5 + 0.5;
    float b = 0.5;
    float a = 1.0;

    // Write the color to the output image
    imageStore(output_image, pixel_coords, vec4(r, g, b, a));
}
