USE DeanValdivia;
GO

-- Tabla de Usuarios
CREATE TABLE Usuarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_completo NVARCHAR(100) NOT NULL,
    correo NVARCHAR(100) UNIQUE NOT NULL,
    usuario NVARCHAR(50) UNIQUE NOT NULL,
    contraseña NVARCHAR(100) NOT NULL,
    es_admin BIT DEFAULT 0
);
GO

-- Tabla de Registros de Alumnos
CREATE TABLE RegistrosAlumnos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    alumno_id INT NOT NULL,
    horario NVARCHAR(50) NOT NULL,
    horas INT NOT NULL CHECK (horas <= 6),
    total_pagar DECIMAL(10,2) NOT NULL,
    pago_id NVARCHAR(20) UNIQUE NOT NULL,
    monto_abonado DECIMAL(10,2) DEFAULT 0.0,
    fecha_pago DATETIME,
    abonado_acumulado DECIMAL(10,2) DEFAULT 0.0,
    falta_actual DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (alumno_id) REFERENCES Usuarios(id)
);
GO

-- Crear usuario administrador
INSERT INTO Usuarios (nombre_completo, correo, usuario, contraseña, es_admin)
VALUES ('Dean Valdivia', 'admin@escuela.com', 'Dean Valdivia', '12345', 1);
GO

-- Procedimiento para generar ID de pago
CREATE PROCEDURE sp_GenerarPagoID
    @pago_id NVARCHAR(20) OUTPUT
AS
BEGIN
    SET @pago_id = 'PAG-' + RIGHT('00000' + CAST(ABS(CHECKSUM(NEWID())) AS NVARCHAR(10)), 5)
END;
GO

-- Procedimiento para nuevo registro
CREATE PROCEDURE sp_CrearRegistro
    @alumno_id INT,
    @horario NVARCHAR(50),
    @horas INT
AS
BEGIN
    IF @horas > 6
    BEGIN
        RAISERROR('Máximo 6 horas permitidas', 16, 1)
        RETURN
    END
    
    DECLARE @total DECIMAL(10,2) = @horas * 50
    DECLARE @pago_id NVARCHAR(20)
    
    EXEC sp_GenerarPagoID @pago_id OUTPUT
    
    INSERT INTO RegistrosAlumnos (
        alumno_id, horario, horas, total_pagar, pago_id,
        monto_abonado, fecha_pago, abonado_acumulado, falta_actual
    )
    VALUES (
        @alumno_id, @horario, @horas, @total, @pago_id,
        0.0, GETDATE(), 0.0, @total
    )
    
    SELECT SCOPE_IDENTITY() AS nuevo_id, @pago_id AS pago_id_generado
END;
GO
