import sys, getopt
from xml.etree import ElementTree
import pandas as pd

#Read arguments from command line
# len(sys.argv) = 3 -> command line containing input and output file path
# len(sys.argv) = 2 -> command line for help
if len(sys.argv) > 3 or len(sys.argv) < 2:
    print("Invalid number of arguments. Please use the following command /getGCPInfo.py <inputfile>.p4d <outputfile>.txt")
    sys.exit()
          
if sys.argv[1] in ("-h", "--Help", "--help"):
   print("getGCPInfo.py <inputfile>.p4d <outputfile>.txt")
   sys.exit()

#get input and output file path   
inputFile = sys.argv[1]
outputFile = sys.argv[2]
          
# create data frame to store GCPs' info
gcp_df = pd.DataFrame(columns = ["label", 'x', 'y', 'z', "tiePoint3D", "type", "id", "numVisibleImg"])

# parse the input xml 
root = ElementTree.parse(inputFile).getroot()

# iterate the parsed xml to get info for each gcp
for gcp_info in root.iter("GCP"):
    label = gcp_info.get("label")
    gcp_df = gcp_df.append({"label": str(gcp_info.get("label")),                       
                          'x': float(gcp_info.get('x')), 'y': float(gcp_info.get('y')), 'z': float(gcp_info.get('z')),
                          "tiePoint3D": str(gcp_info.get("tiePoint3D")), "id": str(gcp_info.get("id")), "type": str(gcp_info.get("type")), 
						  "numVisibleImg": 0}, ignore_index=True)

# clean up the GCPs data frame. Drop the point if it was not full control (? needed?), and reset the index, 
gcp_df.drop(gcp_df.loc[gcp_df["type"] != "3DGCP"].index, axis = 0, inplace = True)
gcp_df.reset_index(drop=True, inplace = True)


# answer to qu1: number of GCPs
numberGCPs = gcp_df.shape[0]
  
  
# answer to qu2: approximate area covered by imported GCPs.
area_x = gcp_df['x'].max() - gcp_df['x'].min()
area_y = gcp_df['y'].max() - gcp_df['y'].min()
area = area_x * area_y


# Preparation for qu3. Read image info
img_GCP_df = pd.DataFrame(columns = ["img_name","GCP_id"])
for img_info in root.iter("image"):
    img_name = str(img_info.get("path")).split("/")[-1]
#    eop_xyz = img_info.find("gps")
#    eop_rpy = img_info.find("ori")                            
    for img_GCP_info in img_info.iter("imageGCP"):
        img_GCP_df = img_GCP_df.append({"img_name":img_name, "GCP_id": str(img_GCP_info.get("id"))}, ignore_index=True)

# remove the line that image couldn't see any GCP
img_GCP_df.drop(img_GCP_df.loc[img_GCP_df["GCP_id"] == ''].index, axis = 0, inplace = True)  

# group the img_GCP_df by GCP_id to get number of visible image per GCP
GCP_img_df = img_GCP_df.groupby(by = "GCP_id", dropna = True).count()
GCP_img_df.rename(columns={"img_name": "img_count"}, inplace = True)
GCP_img_df.reset_index(inplace = True)

#add the number of visible images to gcp_df for each GCP based on GCP id    
for index, row in GCP_img_df.iterrows():
    gcp_id = str(row["GCP_id"])
    #check if the measured GCP is in input GCP list (?needed?) 	
    if(gcp_id not in str(gcp_df["id"])):
       print("Does not find GCP {} from imported GCP list.". format(gcp_id))	   
    gcp_df.loc[gcp_df["id"] == gcp_id, "numVisibleImg"]  = row["img_count"]
	
    
#write to output file    
with open(outputFile, 'w') as text_file:
    text_file.write(str(numberGCPs) + "\n")
    text_file.write(str("%.2f" % area) + "\n")
    for gcp_id, numVisibleImg in  zip(gcp_df["id"], gcp_df["numVisibleImg"]):
          text_file.write("{}: {}".format(gcp_id, numVisibleImg) + "\n")

print("Wrote to {}".format(outputFile))    
