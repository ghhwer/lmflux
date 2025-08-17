import inspect

def check_compatible(function: callable, func_name: str, expected_params: list):
    """
    Check if a function is compatible with the expected signature.

    Args:
    - function (callable): The function to check.
    - func_name (str): The name of the function.
    - expected_params (list): A list of dictionaries containing the expected parameter name, type, and position.

    Returns:
    - function (callable): The original function if it's compatible.

    Raises:
    - AttributeError: If the function is not compatible with the expected signature.
    """
    param_count = 0
    params_match = [False] * len(expected_params)
    signature = inspect.signature(function)
    sigs = {
        param.name: param.annotation
        for param in signature.parameters.values()
    }

    for param_name, py_type in sigs.items():
        for i, expected_param in enumerate(expected_params):
            if (param_name == expected_param['name'] and 
                (expected_param['type'] is None or py_type == expected_param['type']) and 
                param_count == expected_param['position']):
                params_match[i] = True
        param_count += 1

    if all(params_match) and param_count == len(expected_params):
        return function

    correct_sig = f"def {function.__name__}(" + ", ".join([f"{param['name']}: {param['type'].__name__ if param['type'] else 'any'}" for param in expected_params]) + "):..."
    raise AttributeError(f"{func_name} must be defined as {correct_sig}")
