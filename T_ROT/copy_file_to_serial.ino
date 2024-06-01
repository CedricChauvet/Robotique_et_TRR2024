#include <SD.h>
String data[2];
File root;
File myFile;
void setup() {
  Serial.begin(9600);
  pinMode(SDCARD_SS_PIN, OUTPUT);
  SD.begin(SDCARD_SS_PIN);

  delay(5000);
 //Serial.println ("test");
  // Si tu fais un cardinfo.ino, tu obtiens la liste des fichier ainsi tape directements
  String directData = "ESSAI3.CSV";
  openFile(directData);
  //root.rewindDirectory();
  //chercheFichier(root, 0);
  //root.close();
  //openFile(data[0]);
}

void loop() {
  // Nothing happens after setup finishes.

}

void chercheFichier(File dir, int numTabs) {
  int j =0;
  while (true) {
    File entry = dir.openNextFile();
    if (!entry) {
      return;
    }
    String c = entry.name();
    if( c.endsWith("CSV")){
        data[j] = c;
        j=j+1;
    }
    if (entry.isDirectory()) {
      //Serial.println("/");
      chercheFichier(entry, numTabs + 1);
    } else {
      //Serial.print("\t\t");
      //Serial.println(entry.size(), DEC);
    }
    entry.close();
  }
}
 
void openFile(String data){     // ecrit vers le serial tout le fichier

    //Serial.println (data);
    myFile = SD.open(data, FILE_READ);
    while (myFile.available()) {
      //Serial.print("sos");
      Serial.write(myFile.read());
    }
    myFile.close();
    return;
    
  
}
