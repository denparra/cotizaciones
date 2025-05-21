import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)).replace("\\utils", ""))


from utils.excel_utils import preparar_excel

# Prepara y guarda archivo limpio
df_limpio = preparar_excel("export/origen.xlsm", "export/archivo_limpio.xlsx")


print("✅ Archivo limpio generado como 'archivo_limpio.xlsx'. Revisa antes de insertar.")
