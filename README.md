# PolyTop

A topology builder for polymers. [Click here to go to the web app.](https://lilyminium.github.io/polytop/webapp.html)

## Features
Currently PolyTop only supports GROMACS .itp topologies and .pdb coordinates.

## Usage
This relies on the user already having coordinates (.pdbs) and topologies (.itps) for 
each unit fragment of their molecule. You can get these at the [ATB](https://atb.uq.edu.au/).

You may have to manually highlight the PDB file text and paste it into a text document. This 
will get fixed.



### Error reporting

If something is happening that you think shouldn't, please raise an issue or 
email me at 
[lily.wang@anu.edu.au](mailto:lily.wang@anu.edu.au) with the following:
- What you were trying to do
- What it did
- The current state (File > Save universe)
- What you can see in the Javascript console
    - **Firefox**: Ctrl+Shift+K
    - **Chrome**: Ctrl+Shift+I
    - **Safari**: Develop > Show Error Console (turn on Developer tools in Safari > Preferences > Advanced)
    - **Edge**: F12 > Console

    There is likely an error message there in red. If there's a > arrow, try clicking on it
    and screenshotting the error trace.
- Browser and version
- Molecule files

Thank you <3

## To do
- accept all the coordinate formats NGL does
- accept topology formats from other MD engines
- fix z-index placement of unit selection panels
- document
- add interface to customise visualisation past ball+stick
- add animation interface
- highlight fragments in the side-viewport when adding units
- add user guide
- make overlay panels move-able



## Authors

* **Lily Wang** -- <lily.wang@anu.edu.au>

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

This project relies heavily on [NGL](https://github.com/arose/ngl). Even the CSS is largely modified 
from the NGL web app.

* [NGL](https://github.com/arose/ngl)
    - PolyTop relies on NGL for the visualisation and coordinate-handling logic.
    - PolyTop's GUI is based largely off the NGL Web App GUI, which in turn is based off the three.js editor (below)
* [Selectize.js](https://selectize.github.io/selectize.js/) - for the select menus in PolyTop
* [w2ui](http://w2ui.com/web/) - for the GUI layout
* [three.js](http://threejs.org/)
    - NGL relies on three.js to interface with WebGL
* [sprintf.js](https://github.com/alexei/sprintf.js)
    - Both NGL and PolyTop use sprintf to format text
* [jsfeat](http://inspirit.github.io/jsfeat/) - (from NGL)
* [ESDoc](https://esdoc.org/) - for documentation
* [Chroma.js](https://github.com/gka/chroma.js) - (from NGL)
* [FlexiColorPicker](https://github.com/DavidDurman/FlexiColorPicker) - (from NGL)
* [Virtual DOM List](https://github.com/sergi/virtual-list)
* [Font Awesome](http://fontawesome.io) - for icons
* [JS Signals](http://millermedeiros.github.com/js-signals)
* [Lightweight promise polyfill](https://github.com/taylorhakes/promise-polyfill)
* [pako - zlib port](https://github.com/nodeca/pako)
* [Open Source PyMOL](http://sourceforge.net/projects/pymol/) - screen aligned cylinder shader
* [VTK](http://www.vtk.org/) Quadric shader code from the PointSprite Plugin - quadric surface center calculation
* [HyperBalls](http://sourceforge.net/projects/hyperballs/) - hyperball stick shader - Chavent, M., Vanel, A., Tek, A., Levy, B., Robert, S., Raffin, B., &amp; Baaden, M. (2011). GPU-accelerated atom and dynamic bond visualization using hyperballs: a unified algorithm for balls, sticks, and hyperboloids. Journal of Computational Chemistry, 32(13), 2924–35. [doi:10.1002/jcc.21861](https://dx.doi.org/10.1002/jcc.21861)


