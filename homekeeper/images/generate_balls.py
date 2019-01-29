from pathlib import Path
import subprocess


cmdline = "povray +iball.pov +Fn +o{output_path} +W320 +H320 +a0.3 +UA"


colors = [
    "Blue", "Cyan", "Red", "Green", "Yellow", "Black", "Magenta",
]

template = """\
#declare strype_color = {color};

"""

def main():
    for color in colors:
        Path("ball_parameters.inc").write_text(template.format(color=color))
        output_path = f"ball_{color.lower()}_00.png"
        subprocess.run(cmdline.format(output_path=output_path).split())


if __name__ == "__main__":
    main()
