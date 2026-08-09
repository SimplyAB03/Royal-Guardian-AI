import time
import importlib

def run_scan(modules, callback=None):
    total = len(modules)
    results = []

    for index, module_name in enumerate(modules, start=1):
        module = importlib.import_module(module_name)
        result = module.run()
        results.append(result)

        if callback:
            callback(
                module=result["title"],
                percent=int(index / total * 100),
                status=result["status"]
            )

        time.sleep(0.5)

    return results