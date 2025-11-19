Report Engine UML diagrams

Files:
- `report_engine_uml.puml` - PlantUML source describing Django models and the ReportEngine service class.

How to render

Prerequisites:
- Java + PlantUML jar, or the `plantuml` Docker image, or VS Code PlantUML extension.

Using PlantUML jar:
```powershell
# Download plantuml.jar once, then run in the diagrams folder
java -jar C:\path\to\plantuml.jar -tsvg report_engine_uml.puml
# Output: report_engine_uml.svg
```

Using Docker (PowerShell):
```powershell
# From the ReportEngine\diagrams directory
docker run --rm -v ${PWD}:/workspace plantuml/plantuml -tsvg report_engine_uml.puml
```

Using VS Code:
- Install the PlantUML extension, open `report_engine_uml.puml` and click preview or RENDER.

Notes:
- The PlantUML file models the Django `reports_app.models` classes and the `ReportEngine` service class.
- If you'd like, I can attempt to render an SVG here and add it to the `diagrams` folder (requires PlantUML available in the environment).