# Políticas de atención (datos SIMULADOS para el proyecto del curso)

## POL-07 Reembolsos
Un reembolso aprobado se abona en un plazo máximo de 10 días hábiles desde su aprobación.
El ejecutivo debe informar la fecha de aprobación y el plazo restante al cliente.

## POL-12 Escalamiento
Si un caso supera el plazo comprometido, el ejecutivo debe escalarlo a Supervisión y ofrecer al cliente
una nueva fecha de contacto dentro de 48 horas.

## POL-15 Descuento no aplicado
Si el cliente reclama un descuento promocional que no se aplicó en su compra, el ejecutivo verifica que exista
un caso abierto o en revisión de tipo "Descuento no aplicado". El ajuste corresponde a la diferencia entre el
precio cobrado y el precio con descuento, y nunca puede superar el monto reclamado registrado en el caso.
El ajuste se solicita con la herramienta de solicitud de ajuste y queda pendiente de aprobación de un supervisor.

## POL-16 Devolución de dinero
Si el cliente reclama la devolución de dinero por un producto devuelto o un cobro improcedente, el ejecutivo
verifica que exista un caso abierto o en revisión de tipo "Devolución de dinero" o "Reembolso". La devolución
no puede superar el monto reclamado registrado en el caso. Una vez aprobada, se abona según POL-07.

## POL-20 Aprobación humana de ajustes económicos
Todo ajuste económico (descuento o devolución) requiere la aprobación explícita de un supervisor.
El ejecutivo no debe confirmar al cliente que el ajuste está aprobado mientras la solicitud esté pendiente.
Una solicitud no aprobada dentro del plazo vence y debe generarse nuevamente si corresponde.
No se puede generar más de un ajuste por caso.

## POL-21 Casos cerrados
Un caso en estado Cerrado, Resuelto o Cancelado no admite nuevos ajustes. Si el cliente insiste, el ejecutivo
debe abrir un caso nuevo.
