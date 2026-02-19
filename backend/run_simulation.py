# -*- coding: mbcs -*-
import os
from part import *
from material import *
from section import *
from assembly import *
from step import *
from interaction import *
from load import *
from mesh import *
from optimization import *
from job import *
from sketch import *
from visualization import *
from connectorBehavior import *
from abaqus import *
from abaqusConstants import *

class Simulation:
    def __init__(self, model_config, path_data_dir):
        self.fullConfig = model_config
        self.modelName = str(self.fullConfig.keys()[0])
        self.modelBuilder = self.fullConfig[self.modelName]['modelBuilder']
        self.pathDataDir = path_data_dir
        self.backendPath = os.path.dirname(self.pathDataDir)
        self.logFilePath = os.path.join(self.backendPath, "log", "abaqus_log.txt")
        
        Mdb()
        session.journalOptions.setValues(replayGeometry=INDEX, recoverGeometry=INDEX)
        self.model = mdb.Model(name=self.modelName)
        del mdb.models['Model-1']

    def log(self, msg, log_file_path):
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "abaqus_log.txt")

        with open(log_path, "a") as f:
            f.write(msg + "\n")
            f.flush()

    def run(self):
        self._create_materials()
        self._create_parts()
        self._create_sections()
        self._create_steps()
        self._create_partitions()
        self._create_loads()
        self._create_mesh()
        self._create_boundary_conditions()
        self._create_job()

    def _create_materials(self):
        self.log("      - Creating materials...", self.logFilePath)
        mat_params = self.modelBuilder['material']
        jc_params = mat_params['johnsonCook']
        elastic_params = mat_params['elastic']
        
        self.materialJohnsonCook = self.model.Material(name='johnsonCook')

        self.materialJohnsonCook.Plastic(hardening=JOHNSON_COOK, table=((
            jc_params['a'], 
            jc_params['b'], 
            jc_params['n'], 
            jc_params['m'], 
            jc_params['meltingTemp'], 
            jc_params['transitionTemp']), ))
        self.materialJohnsonCook.plastic.RateDependent(table=((
            jc_params['c'], 
            jc_params['epsilonDotZero']), ), type=JOHNSON_COOK)
        
        self.materialJohnsonCook.Elastic(table=((
            elastic_params['youngModulus'], 
            elastic_params['poissonRatio']), ))
        
        self.materialJohnsonCook.Density(table=((mat_params['density'], ), ))

        self.materialElastic = self.model.Material(name='elastic')

        self.materialElastic.Elastic(table=((
            elastic_params['youngModulus'], 
            elastic_params['poissonRatio']), ))
        self.materialElastic.Density(table=((mat_params['density'], ), ))

    def _create_parts(self):
        self.log("      - Creating parts...", self.logFilePath)
        geo_params = self.modelBuilder['geometry']

        lenght_finite_cube = geo_params['lenghtFiniteCube']
        height_finite_cube = geo_params['heightFiniteCube']
        infinite_border = geo_params['infiniteBorder']

        point1_finite_cube = (0.0, infinite_border)
        point2_finite_cube = (lenght_finite_cube, infinite_border + height_finite_cube)

        sketch_finite_cube = self.model.ConstrainedSketch(name='sketch_finite_cube', sheetSize=200.0)
        sketch_finite_cube.sketchOptions.setValues(viewStyle=AXISYM)
        sketch_finite_cube.ConstructionLine(point1=(0.0, 0.0), point2=(0.0, 1.0))
        sketch_finite_cube.rectangle(point1=point1_finite_cube, point2=point2_finite_cube)

        finite_cube_part = self.model.Part(dimensionality=AXISYMMETRIC, name='finiteCube', type=DEFORMABLE_BODY)
        finite_cube_part.BaseShell(sketch=sketch_finite_cube)

        point1_infinite_cube = (0.0, 0.0)
        point2_infinite_cube = (lenght_finite_cube + infinite_border, infinite_border + height_finite_cube)

        sketch_infinite_cube = self.model.ConstrainedSketch(name='sketch_infinite_cube', sheetSize=200.0)
        sketch_infinite_cube.sketchOptions.setValues(viewStyle=AXISYM)
        sketch_infinite_cube.ConstructionLine(point1=(0.0, 0.0), point2=(0.0, 1.0))
        sketch_infinite_cube.rectangle(point1=point1_infinite_cube, point2=point2_infinite_cube)

        infinite_cube_part = self.model.Part(dimensionality=AXISYMMETRIC, name='infiniteCube', type=DEFORMABLE_BODY)
        infinite_cube_part.BaseShell(sketch=sketch_infinite_cube)

        self.rootAssembly = self.model.rootAssembly
        self.rootAssembly.DatumCsysByThreePoints(
            coordSysType=CYLINDRICAL, 
            origin=(0.0, 0.0, 0.0), 
            point1=(1.0, 0.0, 0.0), 
            point2=(0.0, 0.0, -1.0)
            )
        
        finite_cube_instance = self.rootAssembly.Instance(dependent=ON, name='finiteCubeInstance', part=finite_cube_part)
        infinite_cube_instance = self.rootAssembly.Instance(dependent=ON, name='infiniteCubeInstance', part=infinite_cube_part)
        
        self.rootAssembly.InstanceFromBooleanMerge(
            domain=GEOMETRY, 
            instances=(finite_cube_instance, infinite_cube_instance), 
            keepIntersections=ON, 
            name='workpiece', 
            originalInstances=DELETE
            )
        
        del finite_cube_part
        del infinite_cube_part

    def _create_sections(self):
        self.log("      - Creating sections...", self.logFilePath)
        self.workpiecePart = self.model.parts['workpiece']
        geo_params = self.modelBuilder['geometry']
        
        self.model.HomogeneousSolidSection(material='elastic', name='SectionElastic', thickness=None)
        self.model.HomogeneousSolidSection(material='johnsonCook', name='SectionJohnsonCook', thickness=None)
        
        faces_jc = self.workpiecePart.faces.findAt(((
            geo_params['lenghtFiniteCube'] / 2.0, 
            geo_params['heightFiniteCube'] / 2.0 + geo_params['infiniteBorder'], 
            0.0),))
        set_section_jhonson_cook = self.workpiecePart.Set(faces=faces_jc, name='SetSectionJohnsonCook')
        self.workpiecePart.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, 
                                         region=set_section_jhonson_cook, sectionName='SectionJohnsonCook', 
                                         thicknessAssignment=FROM_SECTION)
        
        faces_elastic = self.workpiecePart.faces.findAt(((
            ( geo_params['lenghtFiniteCube'] + geo_params['infiniteBorder']) / 2.0, 
             geo_params['infiniteBorder'] / 2.0, 
             0.0),))
        set_section_elastic = self.workpiecePart.Set(faces=faces_elastic, name='SetSectionElastic')
        self.workpiecePart.SectionAssignment(offset=0.0, offsetField='', offsetType=MIDDLE_SURFACE, 
                                         region=set_section_elastic, sectionName='SectionElastic', 
                                         thicknessAssignment=FROM_SECTION)

    def _create_steps(self):
        self.log("      - Creating steps...", self.logFilePath)
        step_params = self.modelBuilder['step']
        
        self.model.ExplicitDynamicsStep(
            name='ShotPhase', 
            previous='Initial', 
            timePeriod=step_params['durationShotPhase']
        )
        
        self.model.ExplicitDynamicsStep(
            name='RestPhase', 
            previous='ShotPhase',
            timePeriod=step_params['durationRestPhase']
        )

    def _create_partitions(self):
        self.log("      - Creating partitions...", self.logFilePath)
        geo_params = self.modelBuilder['geometry']
        height_finite_cube = geo_params['heightFiniteCube']
        side_interest_region = geo_params['lenghtInterestRegion']
        height_interest_region = geo_params['heightInterestRegion']
        infinite_border = geo_params['infiniteBorder']

        total_height = height_finite_cube + infinite_border

        p1 = self.workpiecePart.DatumPointByCoordinate(
            coords=(side_interest_region, total_height, 0.0)
            )
        p2 = self.workpiecePart.DatumPointByCoordinate(
            coords=(side_interest_region, total_height - height_interest_region, 0.0)
            )
        p3 = self.workpiecePart.DatumPointByCoordinate(
            coords=(0.0, total_height - height_interest_region, 0.0)
            )
        
        faces_jc = self.workpiecePart.faces.findAt(((
            geo_params['lenghtFiniteCube'] / 2.0, 
            geo_params['heightFiniteCube'] / 2.0 + geo_params['infiniteBorder'], 
            0.0),))

        self.workpiecePart.PartitionFaceByShortestPath(
            faces=
            faces_jc, 
            point1= self.workpiecePart.datums[4], 
            point2= self.workpiecePart.datums[5]
            )
        self.workpiecePart.PartitionFaceByShortestPath(
            faces=
            faces_jc, 
            point1= self.workpiecePart.datums[5], 
            point2= self.workpiecePart.datums[6]
            )
        
    def _create_loads(self):
        self.log("      - Creating loads...", self.logFilePath)
        pulse_params = self.modelBuilder['pulse']
        geo_params = self.modelBuilder['geometry']
        total_height = geo_params['heightFiniteCube'] + geo_params['infiniteBorder']
        p0 = pulse_params['p0']
        pMax = pulse_params['pMax']
        rMax = pulse_params['rMax']
        r = pulse_params['r']
        timeMax = pulse_params['timeMax']

        self.model.MappedField(description='', fieldDataType=SCALAR, 
            localCsys=None, name='pulseLoadSpatialProfile', partLevelData=False, 
            pointDataFormat=XYZ, regionType=POINT, 
            xyzPointData=(
                (0.0, total_height, 0.0, p0), 
                (rMax, total_height, 0.0, pMax), 
                (r, total_height, 0.0, 0.0),
                (geo_params['lenghtInterestRegion'], total_height, 0.0, 0.0)
                ))
        
        self.model.TabularAmplitude(
            data=((0.0, 0.0), (timeMax / 2.0, 1.0), (timeMax, 0.0)), 
            name='pulseLoadTemporalProfile',
            smooth=SOLVER_DEFAULT, 
            timeSpan=STEP
            )
        
        self.model.rootAssembly.Surface(
            name='loadSurface', 
            side1Edges= self.rootAssembly.instances['workpiece-1'].edges[10:11]
            )
        
        load = self.model.Pressure(
            amplitude='pulseLoadTemporalProfile', 
            createStepName='ShotPhase', 
            distributionType=FIELD, 
            field='pulseLoadSpatialProfile', 
            magnitude=1.0, 
            name='pulseLoad', 
            region= self.rootAssembly.surfaces['loadSurface']
            )
                
        load.deactivate('RestPhase')
        
    def _create_mesh(self):
        self.log("      - Generating mesh...", self.logFilePath)
        workpiece_edges = self.workpiecePart.edges
        workpiece_faces = self.workpiecePart.faces
        workpiece_part = self.workpiecePart

        interest_region_size = self.modelBuilder['mesh']['interestRegionSize']
        maxElementSize = self.modelBuilder['mesh']['maxElementSize']

        workpiece_part.PartitionFaceByProjectingEdges(
            edges=workpiece_edges[0:1], extendEdges=
            True, faces=workpiece_faces[0:1])
        workpiece_part.PartitionFaceByProjectingEdges(
            edges=workpiece_edges[7:8], extendEdges=
            True, faces=workpiece_faces[0:1])
        workpiece_part.PartitionFaceByShortestPath(faces=
            workpiece_faces[3:4], point1=
            workpiece_part.vertices[2], point2=
            workpiece_part.vertices[9])
        
        workpiece_part.setMeshControls(elemShape=QUAD, 
            regions=workpiece_faces[1:4]+\
            workpiece_faces[5:6], technique=
            STRUCTURED)

        workpiece_part.seedEdgeBySize(constraint=FINER, 
            deviationFactor=0.1, edges=
            workpiece_edges[8:9]+\
            workpiece_edges[12:13]+\
            workpiece_edges[15:17], size=interest_region_size)

        workpiece_part.seedEdgeByBias(biasMethod=SINGLE, 
            constraint=FINER, end1Edges=
            workpiece_edges[7:8]+\
            workpiece_edges[11:12], end2Edges=
            workpiece_edges[5:6]+\
            workpiece_edges[9:10], maxSize=maxElementSize, 
            minSize=interest_region_size)

        workpiece_part.seedEdgeByBias(biasMethod=SINGLE, 
            constraint=FINER, end1Edges=
            workpiece_edges[4:5], end2Edges=
            workpiece_edges[6:7], maxSize=maxElementSize, 
            minSize=interest_region_size)

        workpiece_part.PartitionFaceByProjectingEdges(
            edges=workpiece_edges[5:6], extendEdges=
            True, faces=workpiece_faces[4:5])
        workpiece_part.PartitionFaceByProjectingEdges(
            edges=workpiece_edges[9:10], extendEdges=
            True, faces=workpiece_faces[1:2])

        workpiece_part.setMeshControls(regions=
            workpiece_faces[0:3]+\
            workpiece_faces[6:7], technique=SWEEP)
        workpiece_part.setSweepPath(edge=
            workpiece_edges[0], region=
            workpiece_faces[0], sense=FORWARD)
        workpiece_part.setSweepPath(edge=
            workpiece_edges[4], region=
            workpiece_faces[1], sense=REVERSE)
        workpiece_part.setSweepPath(edge=
            workpiece_edges[8], region=
            workpiece_faces[2], sense=FORWARD)
        workpiece_part.setSweepPath(edge=
            workpiece_edges[17], region=
            workpiece_faces[6], sense=REVERSE)
        workpiece_part.seedEdgeByNumber(constraint=FINER, 
            edges=workpiece_edges[0:1]+\
            workpiece_edges[2:3]+\
            workpiece_edges[4:5]+\
            workpiece_edges[8:9]+\
            workpiece_edges[17:18], number=1)
        workpiece_part.seedEdgeBySize(constraint=FINER, 
            deviationFactor=0.1, edges=
            workpiece_edges[7:8]+\
            workpiece_edges[9:10]+\
            workpiece_edges[14:15]+\
            workpiece_edges[18:19], size=interest_region_size)
        workpiece_part.seedEdgeByBias(biasMethod=SINGLE, 
            constraint=FINER, end1Edges=
            workpiece_edges[3:4], end2Edges=
            workpiece_edges[5:6], maxSize=maxElementSize, 
            minSize=interest_region_size)
        
        workpiece_part.setElementType(
            elemTypes=(ElemType(elemCode=ACAX4, elemLibrary=STANDARD), 
                       ElemType(elemCode=ACAX3, elemLibrary=STANDARD)), 
                       regions=(workpiece_faces[0:3] + workpiece_faces[6:7], ))

        workpiece_part.generateMesh()
        self.model.rootAssembly.regenerate()

    def _create_boundary_conditions(self):
        self.log("      - Creating boundary conditions...", self.logFilePath)
        root_assembly = self.model.rootAssembly

        root_assembly.Set(edges=
            root_assembly.instances['workpiece-1'].edges[13:14]+\
            root_assembly.instances['workpiece-1'].edges[17:18]+\
            root_assembly.instances['workpiece-1'].edges[20:21]
            , name='SetAxissymmetryEdges')
        
        self.model.DisplacementBC(amplitude=UNSET, createStepName=
            'Initial', distributionType=UNIFORM, fieldName='', localCsys=None, name=
            'axisSymmetry', region=root_assembly.sets['SetAxissymmetryEdges'], 
            u1=SET, u2=UNSET, ur3=UNSET)

    def _create_job(self):
        self.log("      - Creating job and processing input file...", self.logFilePath)
        job_name = self.modelName
        step_params = self.modelBuilder['step']
        total_frames = step_params['totalFrames']
        num_cpus = self.modelBuilder['job']['numCPUs']
        
        self.model.fieldOutputRequests['F-Output-1'].setValues(
            variables=('S', 'U', 'PEEQ'), numIntervals=total_frames)
            
        mdb.Job(activateLoadBalancing=False, atTime=None, contactPrint=OFF, 
                description='', echoPrint=OFF, explicitPrecision=SINGLE, historyPrint=OFF, 
                memory=90, memoryUnits=PERCENTAGE, model=self.modelName, modelPrint=OFF, 
                multiprocessingMode=DEFAULT, name='JobMock', nodalOutputPrecision=SINGLE, 
                numCpus=1, numDomains=1, parallelizationMethodExplicit=DOMAIN, queue=None, 
                resultsFormat=ODB, scratch='', type=ANALYSIS, userSubroutine='', waitHours=0, waitMinutes=0)
        
        files_path = os.path.join(self.backendPath, 'files')
        inp_path = os.path.join(files_path, 'inp')
        job_path = os.path.join(files_path, 'job')

        if not os.path.exists(inp_path):
            os.makedirs(inp_path)
        if not os.path.exists(job_path):
            os.makedirs(job_path)

        os.chdir(inp_path)
        mdb.jobs['JobMock'].writeInput()
        self.log("      - Input file for the job created successfully.", self.logFilePath)

        inp_file_path = os.path.join(inp_path, 'JobMock.inp')
        self._modify_element_type(inp_file_path, "ACAX4", "CINAX4")

        os.chdir(job_path)
        mdb.ModelFromInputFile(name=self.modelName + '_infinite', inputFileName= inp_file_path)
        self.log("      - Model created from input file successfully.", self.logFilePath)

        del mdb.jobs['JobMock']

        job = mdb.Job(activateLoadBalancing=False, atTime=None, contactPrint=OFF, 
            description='', echoPrint=OFF, explicitPrecision=SINGLE, historyPrint=OFF, 
            memory=90, memoryUnits=PERCENTAGE, model=self.modelName + '_infinite', modelPrint=OFF, 
            multiprocessingMode=DEFAULT, name=job_name, nodalOutputPrecision=SINGLE, 
            numCpus=num_cpus, numDomains=num_cpus, parallelizationMethodExplicit=DOMAIN, queue=None, 
            resultsFormat=ODB, scratch='', type=ANALYSIS, userSubroutine='', waitHours=
            0, waitMinutes=0)
        
        job.submit(consistencyChecking=OFF)
        self.log("      - Job submitted successfully.", self.logFilePath)

        job.waitForCompletion()
        self.log("      - Job completed successfully.", self.logFilePath)

    def _modify_element_type(self, file_path, old_element, new_element):
        with open(file_path, 'r') as f:
            content = f.read()
        
        new_content = content.replace(old_element, new_element)
        
        with open(file_path, 'w') as f:
            f.write(new_content)