import os
import arcade
from array import array
from arcade.gl import BufferDescription

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN_TITLE = "Arcade Shader Minimal"

SHADER_PATH = os.path.join(os.path.dirname(__file__), "shaders/fragment.glsl")
COMPUTE_SHADER_PATH = os.path.join(os.path.dirname(__file__), "shaders/compute.glsl")


class ShaderWindow(arcade.Window):
    def __init__(self):
        # Request OpenGL 4.3+ for compute shader support
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, resizable=False, gl_version=(4, 3))
        self.quad_fs = arcade.gl.geometry.quad_2d_fs()

        # Load and compile fragment shader
        with open(SHADER_PATH, "r") as f:
            fragment_shader = f.read()

        # Create basic rendering program for visualization
        vertex_shader = """
        #version 330
        in vec2 in_vert;
        in vec2 in_uv;
        out vec2 uv;
        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            uv = in_uv;
        }
        """

        self.render_prog = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)

        # Initialize compute shader if compute shader file exists
        self.compute_shader = None
        if os.path.exists(COMPUTE_SHADER_PATH):
            with open(COMPUTE_SHADER_PATH, "r") as f:
                compute_shader_source = f.read()

            # Replace tokens in the compute shader source if needed
            # You can customize these values or make them configurable
            self.group_x = 32
            self.group_y = 32

            # Preprocess the compute shader source
            compute_shader_source = compute_shader_source.replace("COMPUTE_SIZE_X", str(self.group_x))
            compute_shader_source = compute_shader_source.replace("COMPUTE_SIZE_Y", str(self.group_y))

            self.compute_shader = self.ctx.compute_shader(source=compute_shader_source)

            # Create texture to store compute shader output
            # This will be used as input for the fragment shader
            self.compute_output_texture = self.ctx.texture((SCREEN_WIDTH, SCREEN_HEIGHT), components=4, dtype='f4')

            # Create a simple buffer for compute shader operations if needed
            # This is a simple example - you can customize this to your needs
            initial_data = array('f', [float(i % 256) / 255.0 for i in range(SCREEN_WIDTH * SCREEN_HEIGHT * 4)])  # Example data
            self.compute_ssbo = self.ctx.buffer(data=initial_data)

        # Create a program for displaying the compute shader output
        compute_display_vertex_shader = """
        #version 330
        in vec2 in_vert;
        in vec2 in_uv;
        out vec2 uv;
        void main() {
            gl_Position = vec4(in_vert, 0.0, 1.0);
            uv = in_uv;
        }
        """

        compute_display_fragment_shader = """
        #version 330
        in vec2 uv;
        out vec4 fragColor;
        uniform sampler2D compute_texture;
        void main() {
            fragColor = texture(compute_texture, uv);
        }
        """

        self.compute_display_prog = self.ctx.program(
            vertex_shader=compute_display_vertex_shader,
            fragment_shader=compute_display_fragment_shader
        )

        self.total_time = 0.0

    def on_update(self, delta_time: float):
        self.total_time += delta_time
        # Update time uniform in the rendering program
        self.render_prog["u_time"] = self.total_time

    def run_compute_shader(self, **kwargs):
        """
        Run the compute shader with given input parameters and return the result.

        Args:
            **kwargs: Shader uniforms to set before running the compute shader

        Returns:
            Buffer content after compute shader execution
        """
        if self.compute_shader is None:
            return None

        # Set uniforms passed as keyword arguments
        for key, value in kwargs.items():
            self.compute_shader[key] = value

        # Bind buffers to their bindings
        self.compute_buffer_in.bind_to_storage_buffer(binding=0)
        self.compute_buffer_out.bind_to_storage_buffer(binding=1)

        # Execute compute shader
        self.compute_shader.run(group_x=self.group_x, group_y=self.group_y)

        # Swap input and output buffers for next frame (double buffering)
        self.compute_buffer_in, self.compute_buffer_out = self.compute_buffer_out, self.compute_buffer_in

        # Return the result (content of the output buffer after swapping)
        return self.compute_buffer_in.read()

    def on_draw(self):
        self.clear()

        # Run compute shader if it exists
        if self.compute_shader is not None:
            # Bind the texture to the compute shader as an image
            self.compute_output_texture.bind_to_image(unit=0, read=False, write=True)

            # Set uniforms for the compute shader
            self.compute_shader["u_time"] = self.total_time
            self.compute_shader["u_resolution"] = (SCREEN_WIDTH, SCREEN_HEIGHT)

            # Bind the SSBO to the compute shader if needed
            self.compute_ssbo.bind_to_storage_buffer(binding=1)

            # Run the compute shader
            self.compute_shader.run(group_x=self.group_x, group_y=self.group_y)

        # Render the result of the compute shader
        # Use the default framebuffer (the screen)
        self.compute_output_texture.use(0)  # Use as texture unit 0
        self.compute_display_prog["compute_texture"] = 0
        self.quad_fs.render(self.compute_display_prog)
        

    def on_key_press(self, symbol: int, modifiers: int):
        if symbol == arcade.key.Q:
            arcade.close_window()

def main():
    ShaderWindow()
    arcade.run()


if __name__ == "__main__":
    main()

