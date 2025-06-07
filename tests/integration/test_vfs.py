def process_data(data, callback):
    print(f"Processing {data}...")
    result = data.upper()
    # Chama a função callback com o resultado
    callback(result)

# Função que será passada como callback
def print_result(result):
    print(f"Result: {result}")

# Usando a função com callback
process_data("hello world", print_result)
