# Setup

This file will help you setup the data generation pipeline.

## Automatic Setup

The automatic setup is the easiest way to go, using a bash script provided by us. From the ```src``` folder execute:

```sh
./setup.sh
```

It performs the following:
* creates a virtual python environment in the folder env  
* installs python dependencies
* downloads data sets for NLTK
* if parameter "ubuntu" is specified: first installs system software (python + devtools and virtualenv) (requires sudo)

### Manual Setup
If necessary, you can perform the setup manually:

Install necessary python packages (usage of a virtualenv is highly encouraged; see setup script!)
```sh
pip install -r requirements.txt
```

Download NLTK tokenization data. 
In a python shell execute:
````python
import nltk
nltk.download('punkt')
````

Note, that nltk downloads data outside the project folder to globally minimize storage usage. The data folder will be in the command line output.

If necessary, add the directory to your Python path. (Depends on your operating system and Python setup.)

Create a log directory:
```shell script
mkdir logs
```