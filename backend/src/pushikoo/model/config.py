from pydantic import AliasChoices, BaseModel, Field


class SystemConfig(BaseModel):
    class Network(BaseModel):
        proxies: dict[str, str] = Field(
            default_factory=dict,
            description="Proxy configuration, e.g., {'http': 'http://...', 'https': 'https://...'}",
        )

    class Policy(BaseModel):
        # article_max_ageday: int = Field(
        #     180,
        #     description="Maximum allowed article age in days (older articles are ignored)",
        # )
        perf_merged_details: bool = Field(
            True,
            description="Whether to merge detailed items in performance reports",
        )
        flow_run_timeout_seconds: int = Field(
            600,
            ge=1,
            validation_alias=AliasChoices(
                "flow_run_timeout_seconds", "flow_node_stuck_warning_seconds"
            ),
            description="Terminate a flow instance after it runs for this many seconds",
        )
        warning_retry_max_hours: int = Field(
            24,
            ge=1,
            description="Stop retrying warning deliveries after this many hours",
        )

        class Attempt(BaseModel):
            getter_timeline: list[int] = Field(
                default_factory=lambda: [5, 10, 50],
                description="A warning is triggered after getter_instance.timeline fails several consecutive times",
            )

        attempt: Attempt = Attempt()

    network: Network = Network()
    policy: Policy = Policy()
