# data_cv
Generate custom CV using R and CSS based on `datadrivencv`


# Important Files:

- `setup.Rmd` run the first code chunk to install the necessary R packages. The chunks below that are to instantiate the original CV templates used in the `datadrivencv` library. I have edited these myself and moved my edited versions of `render_cv.r` and `cv_printing_function.r` to the root directory of this repo.

- `cv_printing_functions.r` the printing functions used to print out the text in the `*.csv` files as html/markdown code in the `cv.rmd` that used by pagedown and knitr to actually build the pdf and html. In my version, I added customizations to the functions to help make my CV how I want it. 

- `render_cv.r` used to render the html and pdf version of the CV. Outputs these into `/output/`, which is where the `cv.rmd` template is also located.

- `/output/my_cv.rmd` my edited version of the CV markdown. This folder is also where the rendered pdf and html versions will be placed.

- `css/styles.css` this has the CSS code that I am using specifically when rendering `my_cv.rmd` into the pdf and html versions. Note that this is referenced at the top of `my_cv.rmd`.

- `my_cv_data/*.csv` these csv files are where I record my CV entries. These are read and placed into the `CV` object instantiated at the beginning of `my_cv.rmd`. 


# To run:

If starting from scratch,

1. Have your CV entries in the `*.csv` files in `/my_csv_data/`.

2. Run all the chunks in `setup.Rmd`.

3. You can then `cd output/`

4. Run the `render.r` that was generated in  `output/`. Make sure this `render.r` is pointing to the `cv.rmd` template you want to render.


Otherwise, just run my `render.r` in the root directory of this repo and make sure that all paths are pointing to the correct file. For example:

- my version of `./render.r` is pointing to `./output/my_cv.rmd`,

- `./output/my_cv.rmd` is sourcing `./cv_printing_functions.r`, 

- `./output/my_cv.rmd` is using `./css/styles.css`, and

- `./output/my_cv.rmd` is pointing to the text recorded in the `./my_cv_data/*.csv` files.
