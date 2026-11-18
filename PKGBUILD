# Maintainer: glist
pkgname=liquid-glass-player
pkgver=0.1.0
pkgrel=1
pkgdesc="Minimalist monochrome liquid-glass music player (GTK4 + Libadwaita + GStreamer)"
arch=('any')
url="https://github.com/glistglistovich228eshkere-afk/liquid-glass-player"
license=('MIT')
depends=(
  'python'
  'python-gobject'
  'python-mutagen'
  'gtk4'
  'libadwaita'
  'gstreamer'
  'gst-plugins-base'
  'gst-plugins-good'
  'gst-plugins-bad'
  'gst-libav'
)
makedepends=(
  'python-build'
  'python-installer'
  'python-setuptools'
  'python-wheel'
)
# Requires a git tag named v$pkgver in the upstream repository.
source=("$pkgname-$pkgver.tar.gz::$url/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

build() {
  cd "$srcdir/$pkgname-$pkgver"
  python -m build --wheel --no-isolation
}

package() {
  cd "$srcdir/$pkgname-$pkgver"
  python -m installer --destdir="$pkgdir" dist/*.whl

  install -Dm644 data/liquid-glass.desktop \
    "$pkgdir/usr/share/applications/liquid-glass.desktop"
  install -Dm644 LICENSE "$pkgdir/usr/share/licenses/$pkgname/LICENSE"
}
