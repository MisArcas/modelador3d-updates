#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reconstrucción 3D por fotogrametría para TU3D.

Uso:
  python reconstruir.py escaneo.zip                 (elige el método automáticamente)
  python reconstruir.py carpeta_fotos --metodo openmvs --calidad alta
  python reconstruir.py --solo-posproceso malla.ply (solo limpia y convierte a STL)

Métodos (instalá al menos uno, ver GUIA-ESCANEO.md):
  meshroom : AliceVision Meshroom (meshroom_batch). Necesita GPU NVIDIA (CUDA).
  colmap   : COLMAP automatic_reconstructor con denso. Necesita GPU NVIDIA (CUDA).
  openmvs  : COLMAP (posiciones de cámara, anda sin GPU) + OpenMVS (malla, anda en CPU).

Variables de entorno opcionales para ubicar los programas:
  COLMAP_EXE=C:\\COLMAP\\COLMAP.bat   OPENMVS_DIR=C:\\OpenMVS   MESHROOM_BATCH=C:\\Meshroom\\meshroom_batch.exe
"""
import argparse, glob, os, shutil, subprocess, sys, time, zipfile

IMG_EXT = ('.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG')


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def fail(msg):
    print('\nERROR: ' + msg, file=sys.stderr)
    sys.exit(1)


def find_exe(names, env=None, extra_dirs=()):
    if env and os.environ.get(env):
        p = os.environ[env]
        if os.path.isfile(p):
            return p
        for n in names:
            c = os.path.join(p, n)
            if os.path.isfile(c):
                return c
    for n in names:
        p = shutil.which(n)
        if p:
            return p
    for d in extra_dirs:
        for n in names:
            for c in glob.glob(os.path.join(d, '**', n), recursive=True)[:1]:
                return c
    return None


PF = [os.environ.get('ProgramFiles', r'C:\Program Files'), r'C:\COLMAP', r'C:\OpenMVS', r'C:\Meshroom', os.path.expanduser('~')]


def tools():
    colmap = find_exe(['colmap', 'COLMAP.bat', 'colmap.exe'], 'COLMAP_EXE', [os.path.join(PF[0], 'COLMAP'), r'C:\COLMAP'])
    mvs_dir = os.environ.get('OPENMVS_DIR')
    densify = find_exe(['DensifyPointCloud', 'DensifyPointCloud.exe'], 'OPENMVS_DIR', [os.path.join(PF[0], 'OpenMVS'), r'C:\OpenMVS', '/usr/local/bin/OpenMVS'])
    if densify:
        mvs_dir = os.path.dirname(densify)
    meshroom = find_exe(['meshroom_batch', 'meshroom_batch.exe'], 'MESHROOM_BATCH', [r'C:\Meshroom', os.path.join(PF[0], 'Meshroom')])
    return colmap, mvs_dir, meshroom


def run(cmd, cwd=None):
    log('> ' + ' '.join(f'"{c}"' if ' ' in str(c) else str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], cwd=cwd, shell=(os.name == 'nt' and str(cmd[0]).lower().endswith('.bat')))
    if r.returncode != 0:
        raise RuntimeError(f'El comando falló (código {r.returncode}): {cmd[0]}')


def prepare_images(src, work):
    img_dir = os.path.join(work, 'imagenes')
    os.makedirs(img_dir, exist_ok=True)
    if os.path.isfile(src) and src.lower().endswith('.zip'):
        log(f'Descomprimiendo {src}')
        with zipfile.ZipFile(src) as z:
            for n in z.namelist():
                if n.endswith(IMG_EXT) and not os.path.basename(n).startswith('.'):
                    with z.open(n) as fi, open(os.path.join(img_dir, os.path.basename(n)), 'wb') as fo:
                        shutil.copyfileobj(fi, fo)
    elif os.path.isdir(src):
        for f in os.listdir(src):
            if f.endswith(IMG_EXT):
                shutil.copy2(os.path.join(src, f), img_dir)
    else:
        fail('La entrada tiene que ser un .zip o una carpeta con fotos')
    n = len([f for f in os.listdir(img_dir) if f.endswith(IMG_EXT)])
    if n < 10:
        fail(f'Solo hay {n} fotos. Se necesitan al menos 20 (ideal 40–80).')
    log(f'{n} fotos listas en {img_dir}')
    return img_dir


def via_meshroom(meshroom, img_dir, work):
    out = os.path.join(work, 'meshroom')
    run([meshroom, '--input', img_dir, '--output', out])
    found = glob.glob(os.path.join(out, '**', '*.obj'), recursive=True)
    if not found:
        raise RuntimeError('Meshroom no generó ningún .obj')
    return found[0]


def via_colmap(colmap, img_dir, work, quality, gpu):
    ws = os.path.join(work, 'colmap')
    os.makedirs(ws, exist_ok=True)
    run([colmap, 'automatic_reconstructor', '--workspace_path', ws, '--image_path', img_dir,
         '--quality', quality, '--use_gpu', '1' if gpu else '0', '--dense', '1'])
    for name in ('meshed-poisson.ply', 'meshed-delaunay.ply'):
        found = glob.glob(os.path.join(ws, 'dense', '*', name))
        if found:
            return found[0]
    raise RuntimeError('COLMAP no generó malla (el denso de COLMAP requiere GPU NVIDIA). Probá --metodo openmvs')


def via_openmvs(colmap, mvs_dir, img_dir, work, quality, gpu, video):
    ws = os.path.join(work, 'colmap')
    sparse = os.path.join(ws, 'sparse')
    dense = os.path.join(ws, 'dense')
    os.makedirs(sparse, exist_ok=True)
    db = os.path.join(ws, 'database.db')
    g = '1' if gpu else '0'
    maxsize = {'baja': '1600', 'media': '2400', 'alta': '3200'}[quality]
    run([colmap, 'feature_extractor', '--database_path', db, '--image_path', img_dir,
         '--ImageReader.single_camera', '1', '--SiftExtraction.use_gpu', g, '--SiftExtraction.max_image_size', maxsize])
    if video:
        run([colmap, 'sequential_matcher', '--database_path', db, '--SiftMatching.use_gpu', g])
    else:
        run([colmap, 'exhaustive_matcher', '--database_path', db, '--SiftMatching.use_gpu', g])
    run([colmap, 'mapper', '--database_path', db, '--image_path', img_dir, '--output_path', sparse])
    model = os.path.join(sparse, '0')
    if not os.path.isdir(model):
        raise RuntimeError('COLMAP no pudo ubicar las cámaras. Sacá más fotos con más superposición y textura.')
    run([colmap, 'image_undistorter', '--image_path', img_dir, '--input_path', model, '--output_path', dense, '--output_type', 'COLMAP'])
    exe = lambda n: os.path.join(mvs_dir, n + ('.exe' if os.name == 'nt' else ''))
    mvs = os.path.join(work, 'mvs')
    os.makedirs(mvs, exist_ok=True)
    run([exe('InterfaceCOLMAP'), '-i', dense, '-o', os.path.join(mvs, 'escena.mvs'), '--image-folder', os.path.join(dense, 'images')], cwd=mvs)
    res = {'baja': '2', 'media': '1', 'alta': '0'}[quality]
    run([exe('DensifyPointCloud'), 'escena.mvs', '--resolution-level', res], cwd=mvs)
    run([exe('ReconstructMesh'), 'escena_dense.mvs'], cwd=mvs)
    out = glob.glob(os.path.join(mvs, 'escena_dense_mesh.ply'))
    if not out:
        raise RuntimeError('OpenMVS no generó la malla')
    return out[0]


def postprocess(mesh_path, out_dir, target_mm=None):
    """Limpia la malla (componente principal, agujeros) y exporta STL. Requiere 'trimesh' (opcional)."""
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, 'modelo')
    try:
        import trimesh  # noqa
    except ImportError:
        ext = os.path.splitext(mesh_path)[1]
        shutil.copy2(mesh_path, base + ext)
        log(f'(trimesh no está instalado: copio la malla sin limpiar) -> {base + ext}')
        log('Para limpiar/convertir a STL: pip install trimesh numpy scipy networkx')
        return base + ext
    import trimesh
    log(f'Limpiando {mesh_path}')
    m = trimesh.load(mesh_path, force='mesh', process=True)
    if isinstance(m, trimesh.Scene):
        m = trimesh.util.concatenate(tuple(m.geometry.values()))
    parts = m.split(only_watertight=False)
    if len(parts) > 1:
        m = max(parts, key=lambda p: len(p.faces))
        log(f'Me quedo con la pieza principal ({len(parts)} fragmentos encontrados)')
    m.remove_unreferenced_vertices()
    trimesh.repair.fix_normals(m)
    trimesh.repair.fill_holes(m)
    # Centrar y apoyar en Z=0
    m.apply_translation([-m.bounds.mean(axis=0)[0], -m.bounds.mean(axis=0)[1], -m.bounds[0][2]])
    if target_mm:
        m.apply_scale(target_mm / max(m.extents))
    m.export(base + '.stl')
    ext = m.extents
    log(f'Malla final: {len(m.faces)} triángulos, cerrada={m.is_watertight}, tamaño {ext[0]:.1f} x {ext[1]:.1f} x {ext[2]:.1f} ' + ('mm' if target_mm else '(unidades arbitrarias: ajustá la escala)'))
    if not m.is_watertight:
        log('Aviso: quedó con agujeros. En TU3D usá "Envolvente convexa" o reparala con Meshmixer/Blender (3D Print Toolbox).')
    log(f'Listo -> {base}.stl  (importalo en TU3D con Archivo > Importar malla)')
    return base + '.stl'


def main():
    ap = argparse.ArgumentParser(description='Fotos -> malla 3D (STL) para TU3D')
    ap.add_argument('entrada', nargs='?', help='ZIP exportado por la app o carpeta con fotos')
    ap.add_argument('--metodo', default='auto', choices=['auto', 'meshroom', 'colmap', 'openmvs'])
    ap.add_argument('--calidad', default='media', choices=['baja', 'media', 'alta'])
    ap.add_argument('--sin-gpu', action='store_true', help='Forzar CPU en COLMAP (más lento)')
    ap.add_argument('--video', action='store_true', help='Las fotos vienen de un video (emparejado secuencial, más rápido)')
    ap.add_argument('--salida', help='Carpeta de salida (por defecto, al lado de la entrada)')
    ap.add_argument('--tamano', type=float, help='Escalar para que la medida mayor sea N mm')
    ap.add_argument('--solo-posproceso', metavar='MALLA', help='Solo limpiar una malla existente (.ply/.obj/.stl) y pasarla a STL')
    a = ap.parse_args()

    if a.solo_posproceso:
        out = a.salida or os.path.join(os.path.dirname(os.path.abspath(a.solo_posproceso)), 'resultado')
        postprocess(a.solo_posproceso, out, a.tamano)
        return
    if not a.entrada:
        ap.print_help()
        fail('Indicá el ZIP o la carpeta con fotos (o arrastralo sobre reconstruir.bat)')
    src = os.path.abspath(a.entrada)
    if not os.path.exists(src):
        fail(f'No existe: {src}')
    name = os.path.splitext(os.path.basename(src.rstrip('/\\')))[0]
    work = os.path.join(os.path.dirname(src), name + '_trabajo')
    out = a.salida or os.path.join(os.path.dirname(src), name + '_resultado')
    colmap, mvs_dir, meshroom = tools()
    log(f'COLMAP: {colmap or "no encontrado"} | OpenMVS: {mvs_dir or "no encontrado"} | Meshroom: {meshroom or "no encontrado"}')
    metodo = a.metodo
    if metodo == 'auto':
        metodo = 'openmvs' if (colmap and mvs_dir) else 'meshroom' if meshroom else 'colmap' if colmap else None
    if not metodo:
        fail('No encontré COLMAP, OpenMVS ni Meshroom. Instalalos siguiendo GUIA-ESCANEO.md o definí COLMAP_EXE / OPENMVS_DIR / MESHROOM_BATCH.')
    img_dir = prepare_images(src, work)
    quality = {'baja': 'low', 'media': 'medium', 'alta': 'high'}[a.calidad]
    t0 = time.time()
    try:
        if metodo == 'meshroom':
            if not meshroom: fail('Meshroom no encontrado')
            mesh = via_meshroom(meshroom, img_dir, work)
        elif metodo == 'colmap':
            if not colmap: fail('COLMAP no encontrado')
            mesh = via_colmap(colmap, img_dir, work, quality, not a.sin_gpu)
        else:
            if not (colmap and mvs_dir): fail('Para "openmvs" necesitás COLMAP y OpenMVS')
            mesh = via_openmvs(colmap, mvs_dir, img_dir, work, a.calidad, not a.sin_gpu, a.video)
    except RuntimeError as e:
        fail(str(e))
    log(f'Reconstrucción terminada en {(time.time() - t0) / 60:.1f} min: {mesh}')
    postprocess(mesh, out, a.tamano)


if __name__ == '__main__':
    main()
