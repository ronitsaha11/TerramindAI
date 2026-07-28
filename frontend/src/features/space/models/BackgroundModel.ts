export class BackgroundModel {
  private color: [number, number, number];

  constructor(color: [number, number, number]) {
    this.color = color;
  }

  public getColor(): [number, number, number] {
    return this.color;
  }
}
