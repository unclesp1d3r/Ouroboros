# Agent Monitoring and Configuration

I really want to expand the monitoring and configuration of agents signficantly. Some of this is not yet supported by the v1 of the Agent API, but we can worry about that later (maybe phase 5).

- One of the gripes I get from the users is that they don't know if the cracking agents are actually really running or if they're thrown up on an attack. I think there's no harm in letting user's see all of the agents and what their current state is, though non-admins can't directly control the agents in any way.

- I'd like to be able to see the various GPUs and turn them on-and-off for use by the jobs. That then translates to changing the `backend_device` value in the `advanced_configuration` (see the `contracts/v1_api_swagger.json` for `AdvancedAgentConfiguration`) that eventually becomes the `-d` option in hashcat when the attack is run. It should be a simple toggle.

- When we display the agents in a list, it should be a table with "Agent Name and OS", "Status", "Temperature in Celsius", "Utilization" (this is the average of the assigned enabled devices from the most recent `DeviceStatus` sent by the agent), "Current Attempts per Second", "Average Attempts per Second" (over the last minute, perhaps), and "Current Job" (when we refer to jobs, it should show the Project name, Campaign, and Attack name condensed so users know what the agent is doing at a glance). There should be a gear icon in the last column that pops out a menu that allows the admin to Disable the Agent or go to Details. Everyone can see the list, but only admins can see the gear menu to actually see the agent details. See `contracts/v1_api_swagger.json` for `DeviceStatus`, `HashcatGuess`, and `TaskStatus` for relevant data that is provided by the agent while Attacks/Tasks are running

- We need the ability to add a new agent, which takes a label and which projects the agent is assigned to (displayed as a list of projects with toggles) and it should just be a modal dialog that then shows the agent token so the admin can add the agent.

- In the details view for an agent, the Admin should be able to see tabs with settings, hardware, performance, log, and capabilties.

  - **Settings**

    - Agent Label
      - This is where the admin can control the "label" of the system which is the name shown for the device in the UI.
      - It defaults to the hostname provided by the agent when it registers if this is left blank, but it is a way that the admin can override the name.
      - We haven't yet addressed the idea of the agent display name anywhere in the documentation yet, so we'll need to call it out that this is a thing.
      - Basically `display_name = agent.custom_label or agent.host_name`. The two fields exist on the agent model already, but we should make it clear to Skirmish how agents are displayed now.
    - Enabled
      - This should be a toggle that lets the admin disable the agent from receiving new tasks. The agent will still be alive, but the agent won't get any tasks issued to them when they request one.
    - Agent Update Interval
      - This is the number of seconds between checkins by the agent to the server. It should really default to a random number between 1 and 15, but it currently defaults to 30 seconds.
    - Use Native Hashcat:
      - This is a toggle and it tells the agent not to bother asking the server for a copy of the cracking binary and to just use the one on the agent. It basically sets `AdvancedAgentConfiguration.use_native_hashcat` to True and saves the agent.
    - Enable Additional Hash Types
      - This is a toggle that tells the agent to run all benchmarks when it does its initial capability benchmarks, not just the normal ones. (its basically `--benchmark-all` vs `--benchmark` in hashcat)
    - Projects
      - This should be a list of the projects in the system with toggles so we can decide if the agent is allowed to be assigned jobs for that project.
    - System Info:
      - This is static text that shows the operating system, last seen IP address, client signature, and a agent token. The first three are provided by the agent on connect (see `contracts/v1_api_swagger.json` in `/api/v1/client/agents/{id}`).

  - **Hardware**

    - Computational Units
      - I don't love the name "computational unit" or "backend device", so I welcome suggestions on a better name, but this is the GPUs/CPUs on the agent
      - This actually comes from the agent running hashcat with `--backend-info` on startup and reporting to the server, so it won't be populated until the agent checks in the first time. Until it checks in, we should put a placeholder text and gray out the fieldset.
      - The backend devices are stored in Ouroboros on the Agent model as `list[str]` of their descriptive names in `Agent.devices` and the actual setting of what should be enabled is a comma-seperated list of integers, 1-indexed, so it'll be a little weird to figure out. We'll probably need a better way to do this in the future, but this is a limitation of v1 of the Agent API.
      - This is where the backend devices are listed that are identified by the agent and they can be turned on and off with a toggle (see flowbite small toggle).
      - If there's a running task, we should prompt the admin with three options: restart the running task immediately, let the change apply to the next task to start, or cancel toggling the device.
    - Hardware Acceleration
      - This is also where we should have the ability to set a hardware temperature abort value in celsius. It would translate to the hashcat parameter `--hwmon-temp-abort` on the agent.
      - Perhaps we can hardcode it to 90 util we implement it in the API or just add it as a note, but I don't want to lose this thought so we need to capture this feature.
      - It's not yet implemented in the Agent API, but that would actually be really easy to add without breaking v1. Technically, it can be added to the `AdvancedAgentConfiguration` since v1 of the API does allow additional fields, as long as the required one's are there. The agent will just ignore fields it doesn't know.
      - This should also be where you set the OpenCL device types allowed by hashcat (see `opencl_devices` in `AdvancedAgentConfiguration` in `contracts/v1_api_swagger.json` as well as `--opencl-device-types` in hashcat).
      - This is also where you should be able to toggle CUDA, OpenCL, HIP, and Metal support (which translates to the hashcat parameters `--backend-ignore-cuda`, `--backend-ignore-opencl`, `--backend-ignore-hip`, and `--backend-ignore-metal`) .

  - **Performance**

    - This should just have a nice graph of cracking performance over time. It should show a line chart (see Flowbite charts) showing speed (see `DeviceStatus` in `contracts/v1_api_swagger.json`) with the horizontal axis being time (over the last 8 hours maybe) and the vertical being number of guesses per second (its an `int64`). Each line should be a backend device for this agent.
    - The second should be a set of cards, one for each backend device, containing a circular progress indicator (perhaps we can use flowbite donut charts for this?) current utiliization of the card (based on the most recent `DeviceStatus`) as well as text indicating most recent temperature. If the value is `-1` the the device is not monitored and we can say that.
    - This should update in real-time as new agent TaskStatus records are recieved

  - **Log**

    - This is where the agent errors is displayed. It should be shown in a meaningful timeline with log information and color coding that helps the admin figure out what's going on. I'm pretty open to suggestions on this one.

    - Here's the info in an AgentError object to help guide the discussion:

      ```text
      id: Unique identifier for the error event.
      message: Human-readable error message.
      severity: Severity level of the error.
      error_code: Optional error code for programmatic handling.
      details: Optional structured data with additional error context.
      agent_id: Foreign key to the reporting agent.
      agent: Relationship to the Agent model.
      task_id: Optional foreign key to the related task.
      task: Relationship to the Task model.
      ```

    - It should update in real-time as new AgentError records come in.

  - **Capabilities**

    - This is where the benchmark results go when the agent checks in for the first time. Basically, when the agent runs the first time, or when benchmarks haven't been run in a while, it runs a hashcat benchmark to figure out what types of hashes it can handle. If it is able to benchmark the hashtype without error, it bundles the results up and submits it to the server, along with the speed. We should then display that. We use that data to determine which types of hash lists an agent can get.

    - We are only interested in the last benchmark that we got for the agent.

    - The benchmarks are stored in `app.models.hashcat_benchmark.HashcatBenchmark` and have the following fields:

      ```python
      class HashcatBenchmark(Base):
          """Model for storing hashcat benchmark results for an agent/device/hash type."""

          id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
          agent_id: Mapped[int] = mapped_column(
              Integer, ForeignKey("agents.id"), nullable=False, index=True
          )
          hash_type_id: Mapped[int] = mapped_column(
              Integer, ForeignKey("hash_types.id"), nullable=False
          )
          runtime: Mapped[int] = mapped_column(Integer, nullable=False)  # ms
          hash_speed: Mapped[float] = mapped_column(Float, nullable=False)  # hashes/sec
          device: Mapped[str] = mapped_column(String(length=128), nullable=False)
          created_at: Mapped[datetime] = mapped_column(
              DateTime(timezone=True), default=datetime.utcnow, nullable=False
          )

          agent = relationship("Agent", back_populates="benchmarks")
          hash_type = relationship("HashType")
      ```

    - This should be a table of the hashcat Hash Modes that are successfully benchmarked for the agent.

    - The columns should be:

      - a toggle to disable that hash mode for the agent
      - "Hash ID": which is the numeric hashcat hashmode
      - "Name": the text description of the hashmode
      - "Speed": h/s in SI rounded to SI units (for example, 3.2 Gh/s)
      - "Category": This is taken from the hashcat help and is saved at `docs/current_hashcat_hashmodes.txt` for Skirmish to use as reference

    - The rows should be the roll-up of the hash-mode for all devices and expandable (see "Table with expandable rows" in [Flowbite Advanced Tables](https://flowbite.com/blocks/application/advanced-tables/) for example) where the expanded row shows the same values but for each device.

    - The table should be filterable by category, and searchable by the name or hash ID.

    - The table should include a caption with a date of the last benchmark, and the header should have a button to trigger another updated benchmark, which is done by setting the agent state to `AgentState.pending`.
