Ejecuta el flujo completo de migraciones Django para la app indicada.

Si el usuario no especificó app, inferirla del contexto actual (archivos modificados, modelos tocados). Si no se puede inferir, pregunta antes de continuar.

Pasos a seguir **en orden**:

1. **Verificar modelos pendientes**
   Comprueba si hay cambios en `apps/<app>/models.py` sin migración generada. Si no hay cambios en modelos, informa al usuario y detente salvo que haya pedido explícitamente `migrate` sin `makemigrations`.

2. **`makemigrations`**
   ```
   uv run python manage.py makemigrations <app>
   ```
   - Si la salida contiene "No changes detected", informa y salta al paso 4.
   - Si hay un error de dependencia circular o conflicto, muéstralo y detente — no continúes con `migrate`.

3. **Revisar la migración generada**
   Lee el fichero de migración recién creado (`apps/<app>/migrations/`). Comprueba:
   - Que las operaciones tienen sentido con los cambios del modelo.
   - Que no aparece `RunPython` vacío ni operaciones inesperadas.
   Si algo parece incorrecto, avisa al usuario antes de continuar.

4. **`migrate`**
   ```
   uv run python manage.py migrate
   ```
   Si falla, muestra el error completo e investiga la causa antes de proponer solución.

5. **`check`**
   ```
   uv run python manage.py check
   ```
   Si aparece algún warning o error, reportarlo.

6. Confirma al usuario que todo ha ido bien con un resumen de una línea: qué migración se creó (o si ya estaba al día) y que `migrate` + `check` pasaron sin errores.

**Notas:**
- Siempre usa el prefijo `uv run` para ejecutar comandos Django.
- Nunca uses `--fake`, `--run-syncdb` ni flags destructivos sin confirmación explícita del usuario.
- El `DJANGO_SETTINGS_MODULE` ya está en `.env`, no hace falta exportarlo manualmente.
