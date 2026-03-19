import numpy

init =  (0,0,0,0,0,0,0,0) 

angles = ( -69.047,   44.657,   24.390,   0.0,   22.110,   44.657,  -66.767,   0)
nmb_of_steps = 10
inter=[]
final=[]

for i, angle in enumerate(angles):
    
        #ms = 7 *angle + 1589
    #print("angle: ",angle, " micros :",ms)
    
    if i % 2 == 0:
        for k in range(nmb_of_steps+1):
            new_angle = angle / nmb_of_steps *(k)
            ms = 7 *new_angle + 1589
            #inter.append(int(ms))
            inter.append(round(new_angle,1))
        final. append(inter)
        inter = []
    else:   
        
        for k in range(nmb_of_steps+1):
            new_angle = angle / nmb_of_steps *(k)
            ms = -7 *new_angle + 1589
            #inter.append(int(ms))
            inter.append(round(new_angle,1))
        final. append(inter)
        inter = []
final = numpy.transpose(final)
print repr(str(final).replace('[', '{').replace(']', '}').replace('},', '},\n'))



"""
[[-0.0, -17.26175, -34.5235, -51.78525, -69.047], 
 [0.0, 11.16425, 22.3285, 33.49275, 44.657],
  [0.0, 6.0975, 12.195, 18.2925, 24.39], 
 [-0.0, -0.04175, -0.0835, -0.12525, -0.167],
  [0.0, 5.5275, 11.055, 16.5825, 22.11], 
 [0.0, 11.16425, 22.3285, 33.49275, 44.657], 
 [-0.0, -16.69175, -33.3835, -50.07525, -66.767],
   [-0.0, -0.04175, -0.0835, -0.12525, -0.167]]


table_initial=
[[0, 276, 552, 829, 1105], 
 [0, 475, 950, 1426, 1901], 
 [0, 439, 879, 1319, 1759],
[0, 396, 793, 1190, 1587], 
 [0, 435, 871, 1307, 1743], 
 [0, 475, 950, 1426, 1901], 
 [0, 280, 560, 841, 1121], 
 [0, 396, 793, 1190, 1587]]
 """