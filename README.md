# python_telani_demo
A demonstration of different applications of a proposed telani JSON-Export format.

# prerequisites
Python environment, 
Pip

# Steps to get the python scripts up and running
1) Clone the repo :  git clone "https://github.com/telani-app/python_telani_demo.git"
2) To install all the dependencies run the command : pip install -r .\requirements.txt
3) In the terminal cd to repo : cd path\to\repo
4) Run the command : python main.py
5) In a browser go to the port where the dash application is running.

# How to use the dashboard
The dashboard has three tabs:
  1) Element Type : 
      Here you can select Sensor or Actuator
      Select the element type of the element
      And in the subsequent table there is a list of Sensor/Actuator having the element type you selected.
      If you click on any of the rows of the table, it would generate the QR code associated with the Sensor/Actuator to which the row belongs.
   
   2) Connections : 
      This tab shows the connection graph between the Sensors and the Actuators.
      You can use the play/pause button on top left of the graph to show the different connection graphs , the same can be acheived using a slider below.
   
   3) Graphs : 
      This tab shows two bar graphs for number of elements for a specific element type for Actuators and Sensors respectively.

