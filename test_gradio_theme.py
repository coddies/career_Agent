import gradio as gr
print("Gradio version:", gr.__version__)
try:
    with gr.Blocks(theme=gr.themes.Base()) as demo:
        pass
    print("Blocks accepts theme: YES")
except Exception as e:
    print("Blocks accepts theme: NO", str(e))

try:
    demo.launch(theme=gr.themes.Base(), prevent_thread_lock=True)
    print("Launch accepts theme: YES")
except Exception as e:
    print("Launch accepts theme: NO", str(e))
