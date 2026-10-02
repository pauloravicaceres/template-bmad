import re

filepath = "bmad-control-center/frontend/pages/index.vue"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = re.sub(
    r"<WorkflowStepper\s*:stages=\"stages\"\s*:active-stage-key=\"activeStage\"\s*@select-stage=\"handleSelectStage\"\s*@select-artifact=\"handleSelectArtifactPath\"\s*/>",
    "<WorkflowStepper\n          :stages=\"stages\"\n          :active-stage-key=\"activeStage\"\n          :selected-path=\"selectedPath\"\n          @select-stage=\"handleSelectStage\"\n          @select-artifact=\"handleSelectArtifactPath\"\n        />",
    content
)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)