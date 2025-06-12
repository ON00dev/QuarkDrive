def process_data(data, callback):
    print(f"Processing {data}...")
    result = data.upper()
    # Chama a funcao callback com o resultado
    callback(result)

# Funcao que sera passada como callback
def print_result(result):
    print(f"Result: {result}")

# Usando a funcao com callback
process_data("hello world", print_result)
