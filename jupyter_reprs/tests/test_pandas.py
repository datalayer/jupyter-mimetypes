# Copyright (c) 2023-2024 Datalayer, Inc.
#
# BSD 3-Clause License

import pandas as pd
from jupyter_kernel_client import KernelClient

from jupyter_reprs import DEFAULT_DATA_MIMETYPE, mimebundle_to_object


def test_get_dataframe(jupyter_server):
    port, token = jupyter_server

    data = {
        "Name": [
            "Braund, Mr. Owen Harris",
            "Allen, Mr. William Henry",
            "Bonnell, Miss. Elizabeth",
        ],
        "Age": [22, 35, 58],
        "Sex": ["male", "male", "female"],
    }

    with KernelClient(server_url=f"http://localhost:{port}", token=token) as kernel:
        kernel.execute(f"""import jupyter_reprs
import pandas as pd
df = pd.DataFrame(
    {data}
)""")

        values = kernel.get_variable("df", DEFAULT_DATA_MIMETYPE)

    obj = mimebundle_to_object(values)
    assert isinstance(obj, pd.DataFrame)
    assert obj.equals(pd.DataFrame(data))


def test_get_series(jupyter_server):
    port, token = jupyter_server

    data = [
        "Braund, Mr. Owen Harris",
        "Allen, Mr. William Henry",
        "Bonnell, Miss. Elizabeth",
    ]

    with KernelClient(server_url=f"http://localhost:{port}", token=token) as kernel:
        kernel.execute(f"""import jupyter_reprs
import pandas as pd
df = pd.Series({data}, name="Name")""")

        values = kernel.get_variable("df", DEFAULT_DATA_MIMETYPE)

    obj = mimebundle_to_object(values)
    assert isinstance(obj, pd.Series)
    assert obj.equals(pd.Series(data, name="Name"))
