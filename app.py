from flask import Flask, render_template, request, redirect, url_for, session
import requests

app = Flask(__name__)
app.secret_key = "clave_super_secreta"

API_KEY = "a60788476b1c464aa61639e385e8fbed"




def calcular_tmb(peso, altura, edad, genero):
    """Cálculo de la Tasa Metabólica Basal."""
    if genero == 'hombre':
        return 66 + (13.75 * peso) + (5 * altura) - (6.75 * edad)
    elif genero == 'mujer':
        return 655 + (9.56 * peso) + (1.85 * altura) - (4.68 * edad)
    else:
        raise ValueError("Género no válido.")


def calcular_get(tmb, actividad):
    """Cálculo del Gasto Energético Total según nivel de actividad."""
    factores_actividad = {
        'sedentario': 1.2,
        'ligero': 1.375,
        'moderado': 1.55,
        'alto': 1.725,
        'muy alto': 1.9
    }

    if actividad not in factores_actividad:
        raise ValueError("Nivel de actividad no válido.")

    return tmb * factores_actividad[actividad]


def login_requerido(ruta):
    """Decorador para restringir rutas a usuarios autenticados."""
    def wrapper(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("sesion"))
        return ruta(*args, **kwargs)
    wrapper.__name__ = ruta.__name__
    return wrapper




usuarios = [
    {
        "nombre": "luis",
        "email": "23308060610060@cetis61.edu.mx",
        "contraseña": "123456"
    }
]




@app.route("/")
def home():
    return render_template("index.html")


@app.route("/nutrien")
def nutrien():
    return render_template("nutrien.html")


@app.route('/calculadora', methods=['GET', 'POST'])
def calculadora_tmb_get():
    contexto = {
        'tmb_resultado': None,
        'get_resultado': None,
        'error': None,
        'peso': None,
        'altura': None,
        'edad': None,
        'genero': None,
        'actividad': None
    }

    if request.method == 'POST':
        try:
            contexto['peso'] = request.form.get('peso')
            contexto['altura'] = request.form.get('altura')
            contexto['edad'] = request.form.get('edad')
            contexto['genero'] = request.form.get('genero')
            contexto['actividad'] = request.form.get('actividad')

            if not all([contexto['peso'], contexto['altura'], contexto['edad'], contexto['genero'], contexto['actividad']]):
                raise ValueError("Todos los campos deben estar completos.")

            peso_val = float(contexto['peso'])
            altura_val = float(contexto['altura'])
            edad_val = int(contexto['edad'])

            if peso_val <= 0 or altura_val <= 0 or edad_val <= 0:
                raise ValueError("El peso, la altura y la edad deben ser números positivos.")

            tmb_calc = calcular_tmb(peso_val, altura_val, edad_val, contexto['genero'])
            get_calc = calcular_get(tmb_calc, contexto['actividad'])

            contexto['tmb_resultado'] = f"{tmb_calc:.2f}"
            contexto['get_resultado'] = f"{get_calc:.2f}"

        except ValueError as e:
            contexto['error'] = f"🚨 {str(e)}"
        except Exception as e:
            contexto['error'] = f"🚨 Error inesperado: {str(e)}"

    return render_template('nutrien.html', **contexto)


@app.route("/perfil")
@login_requerido
def perfil():
    return render_template("perfil.html")


@app.route("/sesion")
def sesion():
    return render_template("sesion.html")


@app.route("/iniciar-sesion", methods=["POST"])
def iniciar_sesion():
    email = request.form["email"]
    contraseña = request.form["contraseña"]

    for u in usuarios:
        if u["email"] == email and u["contraseña"] == contraseña:
            session["usuario"] = email
            return redirect(url_for("home"))

    return "Usuario o contraseña incorrectos"


@app.route("/registros")
def registros():
    return render_template("registros.html")


@app.route("/gasto-calorico", methods=["GET", "POST"])
def gasto_calorico():
    resultado_tmb = None
    resultado_get = None
    error = None

    if request.method == "POST":
        try:
            peso = float(request.form["peso"])
            altura = float(request.form["altura"])
            edad = int(request.form["edad"])
            genero = request.form["genero"]
            actividad = request.form["actividad"]

            
            if peso <= 0 or altura <= 0 or edad <= 0:
                raise ValueError("Todos los valores deben ser positivos.")

        
            if genero == "hombre":
                tmb = 66 + (13.75 * peso) + (5 * altura) - (6.75 * edad)
            elif genero == "mujer":
                tmb = 655 + (9.56 * peso) + (1.85 * altura) - (4.68 * edad)
            else:
                raise ValueError("Género no válido.")

            factores = {
                "sedentario": 1.2,
                "ligero": 1.375,
                "moderado": 1.55,
                "alto": 1.725,
                "muy_alto": 1.9
            }

            if actividad not in factores:
                raise ValueError("Nivel de actividad no válido.")

            
            get_total = tmb * factores[actividad]

            resultado_tmb = f"{tmb:.2f}"
            resultado_get = f"{get_total:.2f}"

        except Exception as e:
            error = f"Error: {str(e)}"

    return render_template("gasto_calorico.html",
                        tmb=resultado_tmb,
                        get=resultado_get,
                        error=error)



@app.route("/ingre", methods=["GET", "POST"])
def analizar():
    platillo = ""
    receta = None
    error = None

    if request.method == "POST":
        platillo = request.form.get("platillo")

        if not platillo:
            error = "Debes ingresar un alimento o platillo."
        else:

            
            url = "https://api.spoonacular.com/recipes/complexSearch"

            
            params = {
                "apiKey": API_KEY,
                "query": platillo,
                "number": 1,
                "addRecipeInformation": True
            }

            response = requests.get(url, params=params)

            if response.status_code == 200:
                data = response.json().get("results", [])
                if data:
                    receta = data[0] 
                else:
                    error = "No se encontró ninguna receta para ese platillo."
            else:
                error = "Error al consultar la API."

    return render_template("ingre.html", platillo=platillo, receta=receta, error=error)


@app.route("/cerrar-sesion")
def cerrar_sesion():
    session.pop("usuario", None)
    return redirect(url_for("home"))


@app.route("/registrar", methods=["POST"])
def registrar():
    nombre = request.form["nombre"]
    email = request.form["email"]
    contraseña = request.form["contraseña"]

    usuario = {
        "nombre": nombre,
        "email": email,
        "contraseña": contraseña
    }

    usuarios.append(usuario)
    print(usuarios)

    return redirect(url_for("home"))



if __name__ == "__main__":
    app.run(debug=True)
