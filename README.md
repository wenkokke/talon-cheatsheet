# Talon Voice Commands Cheatsheet

This is a demo for how to get a cheatsheet of all Talon voice commands.

There are two ongoing projects in this repository:

- **Margaret** runs from within Talon.
- **George** runs independently from Talon.

You're probably looking for Margaret.

## Using Margaret

### Install Margaret

1. **Install Talon**

   See [Getting Started][talon-getting-started].

2. **Install Talon Cheatsheet**

   Talon Cheatsheet is written under the assumption that you put the code in your Talon directory,
   _e.g._, `~/.talon`, and that you only copy the code that must be run from within Talon into your
   Talon user directory, _e.g._, `~/.talon/user`.

   On Linux and macOS, run:

   ```bash
   git clone https://github.com/wenkokke/talon-cheatsheet.git ~/.talon/cheatsheet
   mkdir ~/.talon/user/cheatsheet
   cp ~/.talon/cheatsheet/margaret/* ~/.talon/user/cheatsheet/
   ```

   On Windows, run similar commands, using `%AppData%\Talon` instead of `~/.talon`.

3. **Install `docstring_parser`** _(Optional)_

   If `docstring_parser` is installed, Talon Cheatsheet will try to parse the docstrings
   on Talon actions as Sphinx docstrings, and use that information to try and interpolate
   short docstrings to give you better, more readable cheatsheets.

   On Linus and macOS, run:

   ```bash
   ~/.talon/bin/pip install docstring_parser
   ```

   On Windows, run:

   ```batch
   %AppData%\Talon\user\bin pip install docstring_parser
   ```

   _This step is not required for the basic functionality._
   
### Build the cheatsheet

Say `print help` or `print latex help`.

This will generate a self contained HTML or LaTeX file in the `build` subdirectory, _e.g._, `~/.talon/cheatsheet/build`.

### Develop the style sheet

To develop the Sass stylesheet you will need [Node.js][install-npm].

The repository contains both a Sass stylesheet, `assets/sass/style.sass`, and a precompiled CSS stylesheet, `assets/css/style.css`. When you say `print help`, the generated HTML file inlines the precompiled CSS stylesheet.

To build the Sass stylesheet, and overwrite the precompiled CSS stylesheet, run `npm run build-sass`.

To interactively develop the Sass stylesheet, you'll need two things:

1. Use `build/cheatsheet-dev.html` rather than `build/cheatsheet.html`.
   The dev version links directly to the Sass stylesheet.
   To build or rebuild `build/cheatsheet-dev.html`, say `print dev help`.
  
2. From the repository root, run `npm run dev` to start a server which hosts `build/cheatsheet-dev.html`
  and rebuilds the stylesheet when it detects changes.

[talon-getting-started]: https://talonvoice.com/docs/index.html#getting-started
[talon-getting-scripts]: https://talonvoice.com/docs/index.html#getting-scripts
[install-npm]: https://nodejs.org/en/

## Using George

George is still under development.
