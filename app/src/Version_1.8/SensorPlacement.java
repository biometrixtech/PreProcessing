package com.biometrixtech;

import java.io.File;
import java.io.IOException;
import java.nio.charset.Charset;
import org.apache.commons.csv.*;
import org.nd4j.linalg.api.ndarray.INDArray;
import org.nd4j.linalg.api.ops.impl.accum.Dot;
import org.nd4j.linalg.api.ops.impl.accum.Prod;
import org.nd4j.linalg.factory.Nd4j;
import java.util.*;

/**
 * Created by chris on 9/14/16.
 */
public class SensorPlacement {
    public static Set<String> sensNames(CSVRecord columns){
        /* python
        prefix = []
        for i in range(len(columns)):
        name = columns[i]
        name = name[:-2]
        if name not in prefix:
        prefix.append(name)
        return prefix
        */
        Set<String> prefix = new HashSet<String>();
        for(int i = 0; i < 21; i++){
            String name = columns.get(i + 1);
            name = name.substring(0, name.length() - 2);
            prefix.add(name);
        }

        return prefix;

    }

    public static int testTap(List<CSVRecord> data, int sensOffset){
        /* python
        def testTap(data, sens):
            mag = []
            peaks = []
            for i in range(len(data)):
                mag.append(
                    np.sqrt(
                        data[sens+'aX'].ix[i]**2
                        +data[sens+'aY'].ix[i]**2+
                        data[sens+'aZ'].ix[i]**2
                    )
                 ) #calc magnitude
                if mag[i]-mag[i-1] > 2000: #check if deriv of magnitude exceeds threshold
                    peaks.append([i, mag[i]]) #add peak to peak list

            #check for the amount of peaks and assign success or failures
            if len(peaks) >= 3:
                return True
            elif 0 < len(peaks) < 3:
                return 3
            elif len(peaks) == 0:
                return False
         */

        List<Double> mag = new ArrayList<Double>();
        ArrayList<ArrayList<Double>> peaks = new ArrayList<ArrayList<Double>>();

        boolean firstLine = true; //first line is headers, don't process it.
        for (CSVRecord aLine : data) {
            if (!firstLine) {
                int aX = Integer.parseInt(aLine.get(1 + (sensOffset * 7)));
                int aY = Integer.parseInt(aLine.get(1 + (sensOffset * 7) + 1));
                int aZ = Integer.parseInt(aLine.get(1 + (sensOffset * 7) + 2));
                double magnitude = Math.sqrt(Math.pow(aX, 2) + Math.pow(aY, 2) + Math.pow(aZ, 2));
                if (mag.size() > 0 && magnitude - mag.get(mag.size() - 1) > 2000) { // check if deriv of magnitude exceeds threshold
                    ArrayList<Double> indexAndMag = new ArrayList<Double>();
                    indexAndMag.add(new Double(mag.size()));
                    indexAndMag.add(magnitude);
                    peaks.add(indexAndMag);
                }
                mag.add(new Double(magnitude));
            }
            firstLine = false;
        }
        // check for the amount of peaks and assign success or failures
        if (peaks.size() >= 3){
            return 1; // true
        }else if (peaks.size() > 0 && peaks.size() < 3){
            return 2; // fail
        }else{
            return 0; // false
        }
    }

    public static double mean(List<CSVRecord> data, int sensOffset){
        boolean firstLine = true; //first line is headers, don't process it.
        int total = 0;
        int count = 0;
        for (CSVRecord aLine : data) {
            if (!firstLine) {
                int aY = Integer.parseInt(aLine.get(1 + (sensOffset * 7) + 1));
                total += aY;
                count++;
            }
            firstLine = false;
        }
        return (double)total / (double)count;
    }

    public static String[] calculate(List<CSVRecord> list, String checkPlacement){
        CSVRecord columns = list.get(0);
        Set<String> prefixSet = sensNames(columns);
        String prefix[] = prefixSet.toArray(new String[3]);
        String sensorPlacements[] = new String[3];

        int outputs[] = {testTap(list, 0), testTap(list, 1), testTap(list, 2)};

        int trueCount = 0;
        int falseCount = 0;
        int failCount = 0;

        for(int i = 0; i < 3; i++){
            int outputToTest = outputs[i];
            if (outputToTest == 1){
                trueCount++;
            }else if (outputToTest == 0){
                falseCount++;
            }else{
                failCount++;
            }
        }


        /* python
        #interpret the amount of taps as a success or one of two failures
        if response.count(True) == 1 and response.count(False) == 2:
            sensor = response.index(True)
        elif response.count(False) == 3:
            self.status = 'failure2' #not enough detectable taps or no taps
        elif response.count(False) == 2 and response.count(3) == 1:
            self.status = 'failure2' #not enough detectable taps
        elif response.count(False) == 1 or response.count(False) == 0:
            self.status = 'failure3' #two or more sensors experiencing taps or similar at once
         */

        int sensor = 0;
        String status = "";
        if (trueCount == 1 && failCount == 2) {
            for (int i = 0; i < 3; i++) {
                int outputToTest = outputs[i];
                if (outputToTest == 1) {
                    sensor = i;
                }
            }
        }else if (falseCount == 3){
            status = "failure2"; // not enough detectable taps or no taps
        }else if (falseCount == 2 && failCount == 1){
            status = "failure2"; // not enough detectable taps
        }else if (falseCount == 1 || falseCount == 0){
            status = "failure3"; // two or more sensors experiencing taps or similar at once
        }

        if (status != "failure2"     && status != "failure3"){
            /* python
            # find vertical orientation by averaging y-axis
            if sensor == 0:
                orient = np.mean(sens1[prefix[0]+'aY'])
            elif sensor == 1:
                orient = np.mean(sens2[prefix[1]+'aY'])
            elif sensor == 2:
                orient = np.mean(sens3[prefix[2]+'aY'])
             */
            double orient = mean(list, sensor);


            /* python
            #make sure orient is in line with expectation if not throw an error
            if checkPlacement == "H" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[1] = prefix[sensor]
            elif checkPlacement == "H" and orient < 0:
                self.status = 'failure4'

            if checkPlacement == "R" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[2] = prefix[sensor]
            elif checkPlacement == "R" and orient < 0:
                self.status = 'failure4'

            if checkPlacement == "L" and orient > 0:
                self.status = 'success'
                self.sensorPlacement[0] = prefix[sensor]
            elif checkPlacement == "L" and orient < 0:
                self.status = 'failure4'
             */

            if (checkPlacement.equals("H") && orient > 0) {
                status = "success";
                sensorPlacements[1] = prefix[sensor];
            }else if (checkPlacement.equals("H") && orient < 0){
                status = "failure4";
            }

            if (checkPlacement.equals("R") && orient > 0) {
                status = "success";
                sensorPlacements[2] = prefix[sensor];
            }else if (checkPlacement.equals("R") && orient < 0){
                status = "failure4";
            }

            if (checkPlacement.equals("L") && orient > 0) {
                status = "success";
                sensorPlacements[0] = prefix[sensor];
            }else if (checkPlacement.equals("L") && orient < 0){
                status = "failure4";
            }

        }

        /* python
            #make sure one sensor doesn't get assigned to two placements
            dupes = [x for x in self.sensorPlacement if self.sensorPlacement.count(x) > 1]
            if len(dupes) > 0 and dupes[0] != 0:
                self.status = 'failure1'
         */

        int dupes = 0;
        for(int i = 0; i < 3; i++){
            String toTest = sensorPlacements[i];
            for(int j = 0; j < 3; j++){
                String otherOneToTest = sensorPlacements[j];
                if (i != j && toTest != null && otherOneToTest != null && toTest.equals(otherOneToTest)){
                    dupes++;
                }
            }
        }

        if (dupes > 0){
            status = "failure1";
        }

        String result[] = {status, sensorPlacements[0], sensorPlacements[1], sensorPlacements[2]};
        return result;

    }

    public static boolean testCSV(String filename, String expectedResult, String checkPlacement) throws IOException{
        File csvData = new File("/Users/chris/Documents/WorkStuff/biometrix/PreProcessing/app/test/data/sensorPlacement/" + filename);
        CSVParser parser = CSVParser.parse(csvData, Charset.defaultCharset(), CSVFormat.RFC4180);
        List<CSVRecord> list = parser.getRecords();


        // params are data and checkPlacement which is one of "H", "R", and "L" for hip, right foot, and left foot respectively
        String result[] = calculate(list, checkPlacement);
        if (!result[0].equals(expectedResult)) {
            System.out.println("FAIL");
            return false;
        }
        System.out.println("PASS");
        return true;
    }

    public static void main( String[] args ) throws IOException {
        // test all the things

        // Hip Success Test
        testCSV("success_hip.csv", "success", "H");

        //Hip Failure Test
        testCSV("failure2_hip.csv", "failure2", "H");

        //Left Foot Success Test
        testCSV("success_lfoot.csv", "success", "L");

        //Left Foot Failure Test
        testCSV("failure4_lfoot.csv", "failure4", "L");

        //Right Foot Success Test
        testCSV("success_rfoot.csv", "success", "R");

        //Right Foot Failure Test
        testCSV("failure1_rfoot.csv", "failure1", "R");

        //Right Foot Failure Test
        testCSV("failure3_rfoot.csv", "failure3", "R");

    }
}
