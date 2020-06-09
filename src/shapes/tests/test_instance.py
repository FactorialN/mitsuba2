import mitsuba
import pytest
import enoki as ek

from mitsuba.python.test.util import fresolver_append_path

@fresolver_append_path
def example_scene(shape, scale=1.0, translate=[0, 0, 0], angle=0.0):
    from mitsuba.core import xml, ScalarTransform4f as T

    to_world = T.translate(translate) * T.rotate([0, 1, 0], angle) * T.scale(scale)

    shape2 = shape.copy()
    shape2['to_world'] = to_world

    s = xml.load_dict({
        'type' : 'scene',
        'shape' : shape2
    })

    s_inst = xml.load_dict({
        'type' : 'scene',
        'group_0' : {
            'type' : 'shapegroup',
            'shape' : shape
        },
        'instance' : {
            'type' : 'instance',
            "group" : {
                "type" : "ref",
                "id" : "group_0"
            },
            'to_world' : to_world
        }
    })

    return s, s_inst


shapes = [
    { 'type' : 'ply', 'filename' : 'resources/data/ply/sphere.ply' },
    { 'type' : 'rectangle'},
    { 'type' : 'sphere'},
]


@pytest.mark.parametrize("shape", shapes)
def test01_ray_intersect(variant_scalar_rgb, shape):
    from mitsuba.core import Ray3f

    s, s_inst = example_scene(shape)

    # grid size
    n = 21
    inv_n = 1.0 / n

    for x in range(n):
        for y in range(n):
            x_coord = (2 * (x * inv_n) - 1)
            y_coord = (2 * (y * inv_n) - 1)
            ray = Ray3f(o=[x_coord, y_coord + 1, -8], d=[0.0, 0.0, 1.0],
                        time=0.0, wavelengths=[])

            si_found = s.ray_test(ray)
            si_found_inst = s_inst.ray_test(ray)

            assert si_found == si_found_inst

            if si_found:
                si = s.ray_intersect(ray)
                si_inst = s_inst.ray_intersect(ray)

                assert si.prim_index == si_inst.prim_index
                assert si.instance is None
                assert si_inst.instance is not None
                assert ek.allclose(si.t, si_inst.t, atol=2e-2)
                assert ek.allclose(si.time, si_inst.time, atol=2e-2)
                assert ek.allclose(si.p, si_inst.p, atol=2e-2)
                assert ek.allclose(si.sh_frame.n, si_inst.sh_frame.n, atol=2e-2)
                assert ek.allclose(si.dp_du, si_inst.dp_du, atol=2e-2)
                assert ek.allclose(si.dp_dv, si_inst.dp_dv, atol=2e-2)
                assert ek.allclose(si.uv, si_inst.uv, atol=2e-2)
                assert ek.allclose(si.wi, si_inst.wi, atol=2e-2)

                u, v = si.shape.normal_derivative(si)
                u_inst, v_inst = si_inst.instance.normal_derivative(si)

                if ek.norm(u) > 0.0 and ek.norm(v) > 0.0:
                    assert ek.allclose(u, u_inst, atol=2e-2)
                    assert ek.allclose(v, v_inst, atol=2e-2)


@pytest.mark.parametrize("shape", shapes)
def test02_ray_intersect_transform(variant_scalar_rgb, shape):
    from mitsuba.core import Ray3f, ScalarVector3f

    trans = ScalarVector3f([0, 1, 0])
    angle = 15

    for scale in [0.5, 2.7]:
        s, s_inst = example_scene(shape, scale, trans, angle)

        # grid size
        n = 21
        inv_n = 1.0 / n

        for x in range(n):
            for y in range(n):
                x_coord = scale * (2 * (x * inv_n) - 1)
                y_coord = scale * (2 * (y * inv_n) - 1)

                ray = Ray3f(o=ScalarVector3f([x_coord, y_coord, -12]) + trans,
                            d = [0.0, 0.0, 1.0],
                            time = 0.0, wavelengths = [])

                si_found = s.ray_test(ray)
                si_found_inst = s_inst.ray_test(ray)

                assert si_found == si_found_inst

                if si_found:
                    si = s.ray_intersect(ray)
                    si_inst = s_inst.ray_intersect(ray)

                    assert si.prim_index == si_inst.prim_index
                    assert si.instance is None
                    assert si_inst.instance is not None
                    assert ek.allclose(si.t, si_inst.t, atol=2e-2)
                    assert ek.allclose(si.time, si_inst.time, atol=2e-2)
                    assert ek.allclose(si.p, si_inst.p, atol=2e-2)
                    assert ek.allclose(si.dp_du, si_inst.dp_du, atol=2e-2)
                    assert ek.allclose(si.dp_dv, si_inst.dp_dv, atol=2e-2)
                    assert ek.allclose(si.uv, si_inst.uv, atol=2e-2)
                    assert ek.allclose(si.wi, si_inst.wi, atol=2e-2)

                    for shading_frame in [True, False]:
                        u, v = si.normal_derivative(shading_frame)
                        u_inst, v_inst = si_inst.normal_derivative(shading_frame)

                        if ek.norm(u) > 0.0 and ek.norm(v) > 0.0:
                            assert ek.allclose(u, u_inst, atol=2e-2)
                            assert ek.allclose(v, v_inst, atol=2e-2)

