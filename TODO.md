### TODOs

**Science aspects:**

- [ ] Use a few circuits that can easily be scaled to different numbers of qubits. For example, use GHZ as a known structured circuit, plus simple repeated or random gate circuits where the depth can be changed.

- [ ] Verify that the frameworks agree on the results before comparing any timings

- [ ] Measure how runtime and memory grow with the qubit number, and compare that to the expected 2^n scaling of a statevector. Note that runtime also carries the gate count, so the expected growth is n*2^n for GHZ and n^2*2^n for the random and QFT circuits; only the memory should be pure 2^n.

- [ ] Explain the differences I find, looking at the simulation method used, the numerical precision and how the gates are applied.

- [ ] On GPU maybe I can find the qubit count where the GPU becomes faster than the CPU

**Computing aspects:**

- [ ] Select the frameworks (python libraries) to compare, including at least one with GPU support.

- [ ] Define the test circuits once then implement them in each framework's own syntax.

- [ ] Be able to profile the various executions and save the results to a file.

- [ ] Keep the environments reproducible with uv. Keep the repo clean.

- [ ] Schedule the executions on the DTU HPC as batch jobs, on CPU nodes and GPU nodes.

- [ ] Plot the results and write up the conclusions.


**To be prepared:**

- [ ] Write down markdown files that explains the findings
- [ ] Prepare the 15/20 minutes presentation of the findings.