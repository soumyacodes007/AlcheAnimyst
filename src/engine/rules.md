# Manim Code Examples (Community v0.19.0)

This guide provides high-quality, modern examples for the Manim Community library, version v0.19.0 and later. All examples adhere to the latest API standards and best practices.

## Example 1: Basic Shapes and Text

**Description:** Shows a circle and text, then fades them out. This demonstrates basic object creation, positioning with `.next_to()`, and simple animations.

```python
# ### MANIM CODE:
from manim import *
import numpy as np

class BasicShapes(Scene):
    def construct(self):
        # Create a blue circle with some transparency
        circle = Circle(color=BLUE, fill_opacity=0.5)
        # Create text and position it below the circle with a buffer
        text = Text("Hello Manim!").next_to(circle, DOWN, buff=0.5)
        
        # Animate the creation of both objects
        self.play(Create(circle), Write(text), run_time=3)
        self.wait(2)
        # Animate the removal of both objects
        self.play(FadeOut(circle), FadeOut(text), run_time=2)
        
        # Use remaining time for pacing
        self.wait(23)
Use code with caution.
Markdown
Generated text
# ### NARRATION:
Here we create a blue circle and display the text "Hello Manim!" below it. After a brief pause, both elements gracefully fade away, clearing the scene for what comes next.
Use code with caution.
Text
Example 2: Vector Transformation with Labels
Description: Creates a vector, displays a transformation matrix, applies the transformation, and labels the steps, demonstrating .to_corner() and Transform.
Generated python
# ### MANIM CODE:
from manim import *
import numpy as np

class VectorTransform(Scene):
    def construct(self):
        # Setup the coordinate system
        axes = Axes(x_range=[-5, 5, 1], y_range=[-5, 5, 1], x_length=7, y_length=7)
        
        # Define the initial vector and the transformation matrix
        vec_start = np.array([1, 2, 0])
        matrix = np.array([[0, -1], [1, 0]]) # 90 degree rotation matrix

        # Create the visual objects for the vector
        vector = Arrow(ORIGIN, vec_start, buff=0, color=YELLOW)
        vec_label = MathTex("v", color=YELLOW).next_to(vector.get_end(), UR, buff=0.1)
        
        # Animate the initial state
        self.play(Create(axes), Create(vector), Write(vec_label), run_time=5)

        # Display the matrix in the top-left corner
        matrix_tex = MathTex(r"M = \begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix}", color=RED).to_corner(UL)
        self.play(Write(matrix_tex), run_time=3)
        self.wait(2)

        # Calculate the transformed vector and create its visual objects
        vec_end = np.append(np.dot(matrix, vec_start[:2]), 0)
        new_vector = Arrow(ORIGIN, vec_end, buff=0, color=GREEN)
        new_vec_label = MathTex("Mv", color=GREEN).next_to(new_vector.get_end(), UL, buff=0.1)
        
        # Animate the transformation
        self.play(Transform(vector, new_vector), Transform(vec_label, new_vec_label), run_time=5)
        self.wait(4)

        # Fade out everything
        self.play(FadeOut(axes), FadeOut(vector), FadeOut(vec_label), FadeOut(matrix_tex), run_time=3)
        self.wait(8)
Use code with caution.
Python
Generated text
# ### NARRATION:
We start with vector 'v' shown in yellow on a coordinate plane. In the corner, we introduce the 90-degree rotation matrix, M. Now, we apply this matrix to our vector. Watch as vector 'v' smoothly transforms into the new green vector, 'Mv', rotated by 90 degrees. After a moment, the scene clears.
Use code with caution.
Text
Example 3: SinAndCosFunctionPlot (FIXED)
Description: Plots sine and cosine functions on an axis with labels, using modern, correct functions.
Generated python
# ### MANIM CODE:
from manim import *
import numpy as np

class SinAndCosFunctionPlot(Scene):
    def construct(self):
        # Setup axes with specific range and length
        axes = Axes(x_range=[-10, 10, 1], y_range=[-1.5, 1.5, 1], x_length=10, axis_config={"color": GREEN}, tips=False)
        axes_labels = axes.get_axis_labels()
        
        # Plot the two functions
        sin_graph = axes.plot(lambda x: np.sin(x), color=BLUE)
        cos_graph = axes.plot(lambda x: np.cos(x), color=RED)
        
        # Create labels for the graphs
        sin_label = axes.get_graph_label(sin_graph, "\\sin(x)")
        cos_label = axes.get_graph_label(cos_graph, label="\\cos(x)")

        # Animate the creation of the scene
        self.play(Create(axes), Write(axes_labels), run_time=4)
        self.play(Create(sin_graph), Create(cos_graph), run_time=4)
        self.play(Write(sin_label), Write(cos_label), run_time=2)
        
        # Use a vertical line to highlight a point of interest
        # FIXED: Use axes.c2p to get the point for the vertical line
        x_point = 2 * PI
        vert_line = axes.get_vertical_line(axes.c2p(x_point, np.cos(x_point)), color=YELLOW)
        line_label = MathTex(r"x = 2\pi").next_to(vert_line, DOWN)

        self.play(Create(vert_line), Write(line_label), run_time=4)
        self.wait(5)
        
        # Cleanly fade out all elements
        self.play(FadeOut(VGroup(axes, axes_labels, sin_graph, cos_graph, sin_label, cos_label, vert_line, line_label)), run_time=3)
        self.wait(8)
Use code with caution.
Python
Generated text
# ### NARRATION:
Here we plot the sine and cosine functions. The sine function appears in blue, and the cosine function in red. We then label each curve. To highlight a key point, we draw a vertical line at x equals 2 pi, showing its position on the graph. This visualization helps compare the two fundamental trigonometric functions.
Use code with caution.
Text
Example 4: GraphAreaPlot (FIXED)
Description: Demonstrates how to show areas between curves, using modern, correct functions.
Generated python
# ### MANIM CODE:
from manim import *
import numpy as np

class GraphAreaPlot(Scene):
    def construct(self):
        # Setup the axes
        ax = Axes(x_range=[0, 5], y_range=[0, 7], tips=False)
        labels = ax.get_axis_labels()

        # Define and plot two curves
        curve_1 = ax.plot(lambda x: x**2, color=BLUE)
        curve_2 = ax.plot(lambda x: 0.5 * x**2 + 2, color=GREEN)
        
        # Animate the creation of the base graphs
        self.play(Create(ax), Write(labels), run_time=3)
        self.play(Create(curve_1), Create(curve_2), run_time=4)
        
        # Get the area between the two curves over a specific interval
        area = ax.get_area(curve_2, [1, 3], bounded_graph=curve_1, color=GREY, opacity=0.8)
        
        area_label = Text("Area Between Curves").next_to(ax, UP)
        self.play(Write(area_label), run_time=2)
        self.play(FadeIn(area), run_time=3)
        self.wait(5)
        
        # Fade out all elements
        self.play(FadeOut(ax, labels, curve_1, curve_2, area, area_label), run_time=3)
        self.wait(10)
Use code with caution.
Python
Generated text
# ### NARRATION:
In this animation, we visualize the area between two curves. We first plot a blue parabola and a green one. Then, we highlight and fill the area trapped between them from x equals 1 to x equals 3. This is a key concept in integral calculus, and Manim makes it easy to visualize.
