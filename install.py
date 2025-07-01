import subprocess
import sys
import os
from tkinter.filedialog import askdirectory

template_tcl = f'''*templatefileset "C:/Program Files/Altair/2023.1/hwdesktop/templates/feoutput/optistruct/optistruct"
*createstringarray 10 "OptiStruct " " " "ANSA " "PATRAN " "EXPAND_IDS_FOR_FORMULA_SETS "  "ASSIGNPROP_BYHMCOMMENTS" "LOADCOLS_DISPLAY_SKIP " "VECTORCOLS_DISPLAY_SKIP "  "SYSTCOLS_DISPLAY_SKIP " "CONTACTSURF_DISPLAY_SKIP " 
*feinputwithdata2 "#optistruct\\\\optistruct" "{os.path.abspath('./analysis/Output.fem')}" 0 0 0 0 0 1 10 1 0 
*createentity results
set resultid [hm_latestentityid results]
*setvalue results id=$resultid resultfiles="{os.path.abspath('./analysis/Output.h3d')}"
*setvalue results id=$resultid init=1
hm_getresults id=$resultid xml="{os.path.abspath('./analysis/queryconfig.xml')}"zz
'''

template_xml = f'''<root>
	<resource>
		<result file="{os.path.abspath('./analysis/Output.h3d')}" tag="f2"/>
	</resource>
	<settings csvseparator="," omega*t="0" numericprecision="12" idpoolout="NO" poissonsratio="0.500000" numericformat="Fixed" printheader="Yes"/>
	<query id="1" type="Report">
		<hierarchy tag="f2">
			<loadcase id="1" stepindex="0"/>
			<loadcase id="2" stepindex="0"/>
			<loadcase id="3" stepindex="0"/>
		</hierarchy>
		<result type="Element Stresses (2D &amp; 3D)" components="XX XY YY " system="" layers="Mid," corner="" averaging=""/>
		<entity type="Elements" selectionmode="All" selectionlist=""/>
		<sort by="By ID Increasing" type="By Load Case"/>
		<output file="{os.path.abspath('./analysis/Panel.csv')}" complexfilter="" format="Textfile"/>
	</query>
	<query id="2" type="Report">
		<hierarchy tag="f2">
			<loadcase id="1" stepindex="0"/>
			<loadcase id="2" stepindex="0"/>
			<loadcase id="3" stepindex="0"/>
		</hierarchy>
		<result type="Element Stresses (1D):CBAR/CBEAM Axial Stress" components="" system="" layers="" corner="" averaging=""/>
		<entity type="Elements" selectionmode="All" selectionlist=""/>
		<sort by="By ID Increasing" type="By Load Case"/>
		<output file="{os.path.abspath('./analysis/Stringer.csv')}" complexfilter="" format="Textfile"/>
	</query>
</root>
'''

def install_dependencies():
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def write_export_scripts():
    with open("analysis/query.tcl", "w") as file:
        file.write(template_tcl)
    with open("analysis/queryconfig.xml", "w") as file:
        file.write(template_xml)

def write_bat():
    install_dir = askdirectory(title="Select Hypermesh installation directory")
    if not "hwdesktop" in os.listdir(install_dir):
        print("Hyperworks not found at specified install directory")
        exit(1)

    template = f'''del Stringer.csv
del Panel.csv
call "{install_dir}/hwsolvers/scripts/optistruct" Output.fem
del Output.out
del Output.stat
del hwsolver.mesg
call "{install_dir}/hwdesktop/hm/bin/win64/hmbatch" -tcl queryconfig.tcl
del optistruct.msg
del command1.tcl
    '''
    with open("solve.bat", "w") as file:
        file.write(template)

print("Installing dependencies")
install_dependencies()
print("Finished")
print("Preparing solver")
write_export_scripts()
write_bat()
print("Installation complete")