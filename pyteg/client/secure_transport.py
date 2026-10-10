"""Configuración TLS de Qt y comprobación de identidad antes de enviar datos."""

# ruff: noqa: DOC201, DOC501, TRY003, EM101

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtNetwork import QSsl, QSslConfiguration, QSslSocket

from pyteg.network.security import check_certificate

if TYPE_CHECKING:
    from PySide6.QtCore import QObject


def tls_socket(parent: QObject) -> QSslSocket:
    """Prepara TLS 1.3; la invitación verifica la clave exacta del certificado."""
    if not QSslSocket.supportsSsl():
        raise ValueError(
            "Qt no dispone de TLS; instalá el soporte de OpenSSL para conectar"
        )
    connection = QSslSocket(parent)
    configuration = QSslConfiguration.defaultConfiguration()
    configuration.setProtocol(QSsl.SslProtocol.TlsV1_3OrLater)
    configuration.setPeerVerifyMode(QSslSocket.PeerVerifyMode.VerifyNone)
    connection.setSslConfiguration(configuration)
    return connection


def verify_socket(connection: QSslSocket, expected_key: str) -> None:
    """Comprueba la identidad fijada antes de enviar la prueba de ingreso."""
    if not connection.isEncrypted():
        raise ValueError("La conexión todavía no está cifrada")
    check_certificate(bytes(connection.peerCertificate().toDer()), expected_key)
